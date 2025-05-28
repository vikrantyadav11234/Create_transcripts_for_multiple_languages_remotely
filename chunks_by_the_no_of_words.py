import os
import json
import subprocess
from pydub import AudioSegment
from pydub.silence import split_on_silence

# ---- CONFIG ----
AUDIO_DIR = r"D:\Models\audio_data_processing\audio_data\hindi"
TRANSCRIPT_DIR = r"D:\Models\audio_data_processing\audio_data\split_transcript"
TEMP_AUDIO_DIR = "temp_clean_audio"
OUTPUT_AUDIO_DIR = "output/audio_chunks"
OUTPUT_TEXT_DIR = "output/transcript_chunks"
LANGUAGE = "hin"
WORDS_PER_CHUNK = 25

# ---- Ensure directories exist ----
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_TEXT_DIR, exist_ok=True)

def remove_silence(input_path, output_path):
    print(f"Removing silence from {os.path.basename(input_path)}...")
    audio = AudioSegment.from_mp3(input_path)
    chunks = split_on_silence(audio, min_silence_len=300, silence_thresh=audio.dBFS - 16, keep_silence=100)
    if not chunks:
        raise ValueError("No audio chunks found after silence removal.")

    combined = AudioSegment.empty()
    for chunk in chunks:
        combined += chunk
    combined.export(output_path, format="mp3")
    return combined

def run_aeneas_alignment(audio_path, transcript_path, output_json_path):
    print(f"Aligning {os.path.basename(audio_path)}...")
    command = [
        "python", "-m", "aeneas.tools.execute_task",
        audio_path,
        transcript_path,
        f"task_language={LANGUAGE}|is_text_type=plain|os_task_file_format=json",
        output_json_path
    ]
    subprocess.run(command, check=True)

def chunk_by_word_count(audio_path, json_path, file_prefix):
    print(f"Chunking {file_prefix} by {WORDS_PER_CHUNK} words...")
    audio = AudioSegment.from_mp3(audio_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunk_index = 1
    word_buffer = []
    time_buffer = []

    for fragment in data["fragments"]:
        start = float(fragment["begin"])
        end = float(fragment["end"])
        duration = end - start
        text = fragment["lines"][0].strip()
        words = text.split()

        if not words:
            continue

        word_duration = duration / len(words)
        for i, word in enumerate(words):
            word_start = start + i * word_duration
            word_end = word_start + word_duration
            word_buffer.append(word)
            time_buffer.append((word_start, word_end))

            if len(word_buffer) == WORDS_PER_CHUNK:
                export_chunk(audio, word_buffer, time_buffer, file_prefix, chunk_index)
                chunk_index += 1
                word_buffer = []
                time_buffer = []

    # Save any leftover words
    if word_buffer:
        export_chunk(audio, word_buffer, time_buffer, file_prefix, chunk_index)

def export_chunk(audio, words, times, prefix, index):
    chunk_name = f"{prefix}_chunk_{index:03}"
    audio_filename = os.path.join(OUTPUT_AUDIO_DIR, f"{chunk_name}.wav")
    text_filename = os.path.join(OUTPUT_TEXT_DIR, f"{chunk_name}.txt")

    start_ms = int(times[0][0] * 1000)
    end_ms = int(times[-1][1] * 1000)
    chunk_audio = audio[start_ms:end_ms]
    chunk_audio.set_frame_rate(16000).set_channels(1).export(audio_filename, format="wav")

    with open(text_filename, "w", encoding="utf-8") as tf:
        tf.write(" ".join(words))

    print(f"Saved chunk: {chunk_name}")

def process_all_files():
    for audio_file in os.listdir(AUDIO_DIR):
        if not audio_file.endswith(".mp3"):
            continue

        filename = os.path.splitext(audio_file)[0]
        raw_audio_path = os.path.join(AUDIO_DIR, audio_file)
        transcript_path = os.path.join(TRANSCRIPT_DIR, f"{filename}.txt")
        cleaned_audio_path = os.path.join(TEMP_AUDIO_DIR, f"{filename}_clean.mp3")
        alignment_json = f"temp_alignment_{filename}.json"

        if not os.path.exists(transcript_path):
            print(f"Transcript for {filename} not found. Skipping.")
            continue

        try:
            remove_silence(raw_audio_path, cleaned_audio_path)
            run_aeneas_alignment(cleaned_audio_path, transcript_path, alignment_json)
            chunk_by_word_count(cleaned_audio_path, alignment_json, filename)
        finally:
            if os.path.exists(alignment_json):
                os.remove(alignment_json)

if __name__ == "__main__":
    process_all_files()
