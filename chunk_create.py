import argparse  
import logging  
import os  
import random  
import time  
import uuid  
from pathlib import Path  
from concurrent.futures import ThreadPoolExecutor, as_completed  
from pydub import AudioSegment  
from tqdm import tqdm  
  
# Language folder mapping  
LANG_MAP = {  
    "bengali": "ben",  
    "english": "eng",  
    "gujarati": "guj",  
    "hindi": "hin",  
    "kannada": "kan",  
    "malayalam": "mal",  
    "marathi": "mar",  
    "punjabi": "pan",  
    "tamil": "tam",  
    "telugu": "tel"  
}  
  
# Configuration (hardcoded parameters)  
INPUT_ROOT = Path("/home/jupyter/myfiles/symphony/fullaudio")  
OUTPUT_ROOT = Path("/home/jupyter/myfiles/symphony/chunks")  
CHUNK_LENGTH_SEC = 10  # Duration of each chunk in seconds  
TRAIN_RATIO = 0.9  # Ratio: 90% train, 10% dev  
  
  
def create_output_folders(output_root: Path):  
    """Create the folder structure.  
    For each split ("train" and "dev"), a subfolder is created for each language code.  
    """  
    for split in ["train", "dev"]:  
        for code in LANG_MAP.values():  
            (output_root / split / code).mkdir(parents=True, exist_ok=True)  
  
  
def split_and_save_chunks(audio_path: Path, lang_code: str, output_root: Path,  
                          chunk_length_sec: int, train_ratio: float = 0.9):  
    """Loads an MP3 audio file, converts it to mono & 16kHz,  
    splits it into fixed-length chunks, and exports each chunk as a WAV file  
    into train and dev folders.  
  
    The exported chunk's file name follows this naming convention:  
        <6-character token>---<start_time>-<end_time>.wav  
    where start_time and end_time are formatted as "0000.000".  
    """  
    try:  
        audio = AudioSegment.from_mp3(audio_path)  
    except Exception as e:  
        logging.error(f"Error loading {audio_path}: {e}")  
        return  
  
    # Convert to mono and set sample rate to 16kHz  
    audio = audio.set_channels(1).set_frame_rate(16000)  
    duration_ms = len(audio)  
  
    chunks = []  
    # Create fixed-length chunks  
    for i in range(0, duration_ms, chunk_length_sec * 1000):  
        start_ms = i  
        end_ms = min(i + chunk_length_sec * 1000, duration_ms)  
        chunk = audio[start_ms:end_ms]  
  
        # Generate a unique token with 6 characters  
        unique_token = uuid.uuid4().hex[:6]  
        # Compute start and end times (in seconds)  
        start_sec = start_ms / 1000  
        end_sec = end_ms / 1000  
        # Format times as "0000.000"  
        start_str = f"{start_sec:08.3f}"  
        end_str = f"{end_sec:08.3f}"  
        # Build the file name: e.g., a1b2c3---0000.000-0010.000.wav  
        chunk_name = f"{unique_token}---{start_str}-{end_str}.wav"  
        chunks.append((chunk, chunk_name))  
  
    if not chunks:  
        logging.warning(f"No chunks generated for {audio_path}")  
        return  
  
    # Shuffle and split into train and dev sets  
    random.shuffle(chunks)  
    split_idx = int(len(chunks) * train_ratio)  
    train_chunks = chunks[:split_idx]  
    dev_chunks = chunks[split_idx:]  
  
    for chunk, fname in train_chunks:  
        out_path = output_root / "train" / lang_code / fname  
        try:  
            chunk.export(out_path, format="wav")  
        except Exception as e:  
            logging.error(f"Error exporting {out_path}: {e}")  
  
    for chunk, fname in dev_chunks:  
        out_path = output_root / "dev" / lang_code / fname  
        try:  
            chunk.export(out_path, format="wav")  
        except Exception as e:  
            logging.error(f"Error exporting {out_path}: {e}")  
  
  
def gather_files(input_root: Path, selected_lang: str = None):  
    """If selected_lang is provided, only gathers .mp3 files from that language folder.  
    Otherwise, iterates through all language folders.  
    """  
    files = []  
    if selected_lang:  
        # Construct the folder path for the specified language  
        lang_folder = input_root / selected_lang  
        if not lang_folder.exists() or not lang_folder.is_dir():  
            logging.error(f"Selected language folder '{lang_folder}' does not exist.")  
            return files  
        lang_code = LANG_MAP.get(selected_lang.lower())  
        if not lang_code:  
            logging.error(f"Unknown language: {selected_lang}")  
            return files  
        for audio_file in lang_folder.rglob("*.mp3"):  
            files.append((audio_file, lang_code))  
    else:  
        # Fallback to processing all language folders  
        for lang_folder in input_root.iterdir():  
            if not lang_folder.is_dir():  
                continue  
            lang_key = lang_folder.name.lower()  
            lang_code = LANG_MAP.get(lang_key)  
            if not lang_code:  
                logging.warning(f"Skipping unknown language folder: {lang_folder.name}")  
                continue  
            for audio_file in lang_folder.rglob("*.mp3"):  
                files.append((audio_file, lang_code))  
    return files  
  
  
def process_all(input_root: Path, output_root: Path, chunk_length_sec: int,  
                train_ratio: float, selected_lang: str = None):  
    """Processes the MP3 files concurrently: splits them into chunks and exports them as WAV files  
    into train and dev folders. When selected_lang is specified, only that language folder is processed.  
    """  
    create_output_folders(output_root)  
    files_to_process = gather_files(input_root, selected_lang)  
    logging.info(f"Total files to process: {len(files_to_process)}")  
  
    start_time = time.time()  
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:  
        future_to_file = {  
            executor.submit(split_and_save_chunks, file, lang, output_root, chunk_length_sec, train_ratio): (file, lang)  
            for file, lang in files_to_process  
        }  
        for future in tqdm(as_completed(future_to_file), total=len(future_to_file),  
                           desc="Processing audio files", unit="file"):  
            file, lang = future_to_file[future]  
            try:  
                future.result()  
            except Exception as e:  
                logging.error(f"Error processing {file} ({lang}): {e}")  
  
    elapsed = time.time() - start_time  
    logging.info(f"✅ Done. Total elapsed time: {elapsed:.2f} seconds")  
  
  
def main():  
    # Use argparse to require the language folder name, e.g., "english"  
    parser = argparse.ArgumentParser(description="Process mp3 audio files from a single language folder into chunks.")  
    parser.add_argument("--language", "-l", required=True,  
                        help="The name of the language folder to process (e.g., english)")  
    args = parser.parse_args()  
    process_all(INPUT_ROOT, OUTPUT_ROOT, CHUNK_LENGTH_SEC, TRAIN_RATIO, args.language)  
  
  
if __name__ == "__main__":  
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")  
    main()  