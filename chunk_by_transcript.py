import os
import json
import subprocess
from pydub import AudioSegment

# ---- CONFIG ----
AUDIO_DIR = r"D:\Models\audio_data_processing\audio_data\hindi"
TRANSCRIPT_DIR = r"D:\Models\audio_data_processing\audio_data\split_transcript"
OUTPUT_AUDIO_DIR = "output/audio_chunks"
OUTPUT_TEXT_DIR = "output/transcript_chunks"
LANGUAGE = "hin"  # Adjust if necessary

# ---- Ensure output directories exist ----
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_TEXT_DIR, exist_ok=True)

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

def chunk_audio(audio_path, json_path, file_prefix):
    print(f"Processing {file_prefix}...")
    audio = AudioSegment.from_mp3(audio_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for i, fragment in enumerate(data["fragments"]):
        start_ms = int(float(fragment["begin"]) * 1000)
        end_ms = int(float(fragment["end"]) * 1000)
        sentence = fragment["lines"][0].strip()

        chunk_name = f"{file_prefix}_chunk_{i+1:03}"
        audio_filename = os.path.join(OUTPUT_AUDIO_DIR, f"{chunk_name}.wav")
        text_filename = os.path.join(OUTPUT_TEXT_DIR, f"{chunk_name}.txt")

        chunk_audio = audio[start_ms:end_ms]
        # chunk_audio.export(audio_filename, format="wav")
        chunk_audio.set_frame_rate(16000).set_channels(1).export(audio_filename, format="wav")
        with open(text_filename, "w", encoding="utf-8") as tf:
            tf.write(sentence)

    print(f"Saved {i+1} chunks for {file_prefix}")

def process_all_files():
    for audio_file in os.listdir(AUDIO_DIR):
        if not audio_file.endswith(".mp3"):
            continue

        filename = os.path.splitext(audio_file)[0]
        audio_path = os.path.join(AUDIO_DIR, audio_file)
        transcript_path = os.path.join(TRANSCRIPT_DIR, f"{filename}.txt")
        alignment_json = f"temp_alignment_{filename}.json"

        if not os.path.exists(transcript_path):
            print(f"Transcript for {filename} not found. Skipping.")
            continue

        try:
            run_aeneas_alignment(audio_path, transcript_path, alignment_json)
            chunk_audio(audio_path, alignment_json, filename)
        finally:
            if os.path.exists(alignment_json):
                os.remove(alignment_json)

if __name__ == "__main__":
    process_all_files()
