import os
from pydub import AudioSegment
import whisperx
import torch
import math

# ---- CONFIG ----
AUDIO_DIR = r"D:\Models\audio_data_processing\audio_data\sample_audio"
TRANSCRIPT_DIR = r"D:\Models\audio_data_processing\audio_data\sample_transcript"
OUTPUT_AUDIO_DIR = "output_1/audio_chunks"
OUTPUT_TEXT_DIR = "output_1/transcript_chunks"
MODEL_NAME = "small"

# ---- Ensure output directories exist ----
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_TEXT_DIR, exist_ok=True)

# ---- Device detection ----
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device.upper()}")

# ---- Choose compute type based on device ----
if device == "cuda":
    compute_type = "float16"
else:
    compute_type = "int8"  # safer and faster for CPU

# ---- Load WhisperX model ----
model = whisperx.load_model(MODEL_NAME, device, compute_type=compute_type)

def process_audio_file(audio_path, transcript_path):
    print(f"Processing: {os.path.basename(audio_path)}")

    # Transcribe audio and get timestamps
    result = model.transcribe(audio_path)

    audio = AudioSegment.from_mp3(audio_path)
    file_prefix = os.path.splitext(os.path.basename(audio_path))[0]

    # Read transcript
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # Split transcript into chunks by word count (e.g., 10 words per chunk)
    words = transcript.split()
    chunk_size = 10  # You can adjust this number to chunk by a different word count
    num_chunks = math.ceil(len(words) / chunk_size)

    for i in range(num_chunks):
        start_word = i * chunk_size
        end_word = (i + 1) * chunk_size
        chunk_text = " ".join(words[start_word:end_word])

        # Find the corresponding start and end times for this chunk
        start_time = None
        end_time = None
        current_word_index = 0

        for segment in result["segments"]:
            segment_words = segment["text"].split()
            segment_start = segment["start"]
            segment_end = segment["end"]

            # Check if this segment contains any of the chunk words
            for word in segment_words:
                if current_word_index >= start_word and current_word_index < end_word:
                    if start_time is None:
                        start_time = segment_start
                    end_time = segment_end
                current_word_index += 1

        if start_time is None or end_time is None:
            print(f"Skipping chunk {i+1} for {file_prefix} due to no time match")
            continue

        # Convert start and end times to milliseconds
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)

        chunk_name = f"{file_prefix}_chunk_{i+1:03}"
        audio_filename = os.path.join(OUTPUT_AUDIO_DIR, f"{chunk_name}.wav")
        text_filename = os.path.join(OUTPUT_TEXT_DIR, f"{chunk_name}.txt")

        # Extract and save audio chunk
        chunk_audio = audio[start_ms:end_ms]
        chunk_audio.set_frame_rate(16000).set_channels(1).export(audio_filename, format="wav")

        # Save text transcript for this chunk
        with open(text_filename, "w", encoding="utf-8") as f:
            f.write(chunk_text)

    print(f"Saved {num_chunks} chunks for {file_prefix}\n")

def process_all_files():
    for audio_file in os.listdir(AUDIO_DIR):
        if audio_file.endswith(".mp3"):
            filename = os.path.splitext(audio_file)[0]
            audio_path = os.path.join(AUDIO_DIR, audio_file)
            transcript_path = os.path.join(TRANSCRIPT_DIR, f"{filename}.txt")

            if not os.path.exists(transcript_path):
                print(f"Transcript for {filename} not found. Skipping.")
                continue

            process_audio_file(audio_path, transcript_path)

if __name__ == "__main__":
    process_all_files()
