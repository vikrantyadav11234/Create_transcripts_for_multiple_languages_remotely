import os
import json
import subprocess
from pydub import AudioSegment
# import aeneas

# ---- CONFIG ----
AUDIO_DIR = r"D:\Models\audio_data_processing\audio_data\hindi"
TRANSCRIPT_DIR = r"D:\Models\audio_data_processing\audio_data\split_transcript"
OUTPUT_AUDIO_DIR = "output/audio_chunks"
OUTPUT_TEXT_DIR = "output/transcript_chunks"
LANGUAGE = "hin"
WORDS_PER_CHUNK = 15

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

def chunk_by_word_count(audio_path, json_path, file_prefix):
    print(f"Processing {file_prefix} by {WORDS_PER_CHUNK} words per chunk...")
    audio = AudioSegment.from_mp3(audio_path)
    audio_duration_sec = len(audio) / 1000.0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunk_index = 1
    word_buffer = []
    time_buffer = []
    prev_end = 0.0  # Start of the timeline

    for fragment in data["fragments"]:
        start = float(fragment["begin"])
        end = float(fragment["end"])
        duration = end - start
        text = fragment["lines"][0].strip()
        words = text.split()

        # Insert silence chunk if there's a gap between previous and current fragment
        if start > prev_end:
            export_chunk(audio, [], [(prev_end, start)], file_prefix, chunk_index)
            chunk_index += 1

        if not words:
            # Still export an empty chunk if there's time range with no text
            export_chunk(audio, [], [(start, end)], file_prefix, chunk_index)
            chunk_index += 1
            prev_end = end
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

        prev_end = end

    # Remaining words
    if word_buffer:
        export_chunk(audio, word_buffer, time_buffer, file_prefix, chunk_index)
        chunk_index += 1

    # Handle trailing silence at the end of the audio
    if prev_end < audio_duration_sec:
        export_chunk(audio, [], [(prev_end, audio_duration_sec)], file_prefix, chunk_index)

def export_chunk(audio, words, times, prefix, index):
    chunk_name = f"{prefix}_chunk_{index:03}"
    audio_filename = os.path.join(OUTPUT_AUDIO_DIR, f"{chunk_name}.wav")
    text_filename = os.path.join(OUTPUT_TEXT_DIR, f"{chunk_name}.txt")

    start_ms = int(times[0][0] * 1000)
    end_ms = int(times[-1][1] * 1000)
    chunk_audio = audio[start_ms:end_ms]

    chunk_audio.set_frame_rate(16000).set_channels(1).export(audio_filename, format="wav")

    with open(text_filename, "w", encoding="utf-8") as tf:
        tf.write(" ".join(words))  # Will be blank for silent chunks

    print(f"Saved chunk: {chunk_name} ({end_ms - start_ms} ms, {' '.join(words) or 'SILENCE'})")

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
            chunk_by_word_count(audio_path, alignment_json, filename)
        finally:
            if os.path.exists(alignment_json):
                os.remove(alignment_json)

if __name__ == "__main__":
    process_all_files()
