import os
from pydub import AudioSegment
import whisperx
import torch

# ---- CONFIG ----
AUDIO_DIR = r"D:\Models\audio_data_processing\audio_data\sample_audio"
OUTPUT_AUDIO_DIR = "output/audio_chunks"
OUTPUT_TEXT_DIR = "output/transcript_chunks"
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

def process_audio_file(audio_path):
    print(f"Processing: {os.path.basename(audio_path)}")

    result = model.transcribe(audio_path)

    audio = AudioSegment.from_mp3(audio_path)
    file_prefix = os.path.splitext(os.path.basename(audio_path))[0]

    for i, segment in enumerate(result["segments"]):
        start_ms = int(segment["start"] * 1000)
        end_ms = int(segment["end"] * 1000)
        text = segment["text"].strip()

        chunk_name = f"{file_prefix}_chunk_{i+1:03}"
        audio_filename = os.path.join(OUTPUT_AUDIO_DIR, f"{chunk_name}.wav")
        text_filename = os.path.join(OUTPUT_TEXT_DIR, f"{chunk_name}.txt")

        chunk_audio = audio[start_ms:end_ms]
        chunk_audio.set_frame_rate(16000).set_channels(1).export(audio_filename, format="wav")

        with open(text_filename, "w", encoding="utf-8") as f:
            f.write(text)

    print(f"Saved {i+1} chunks for {file_prefix}\n")

def process_all_files():
    for audio_file in os.listdir(AUDIO_DIR):
        if audio_file.endswith(".mp3"):
            audio_path = os.path.join(AUDIO_DIR, audio_file)
            process_audio_file(audio_path)

if __name__ == "__main__":
    process_all_files()
