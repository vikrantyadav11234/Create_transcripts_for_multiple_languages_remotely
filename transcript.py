import os
import io
import shutil
import pathlib
from google.cloud import speech
from pydub import AudioSegment

# Set your credentials JSON path
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/vikrant/youtube_downloader/gstt_json.json"

# Input and output directories
INPUT_DIR = "/home/vikrant/youtube_downloader/test"
OUTPUT_DIR = "/home/vikrant/youtube_downloader/hindi_transcripts_2"

# Make sure output root exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Google Speech client
client = speech.SpeechClient()

def convert_audio(input_path):
    """Convert audio to mono, 16-bit, 16kHz WAV format required by GSTT."""
    sound = AudioSegment.from_file(input_path)
    sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)

    temp_path = input_path + "_converted.wav"
    sound.export(temp_path, format="wav")
    return temp_path

def transcribe_audio(audio_path):
    """Transcribe audio using Google Speech-to-Text API."""
    with io.open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="hi-IN",  # Hindi (can still recognize English parts)
        enable_automatic_punctuation=True
    )

    response = client.recognize(config=config, audio=audio)
    transcript = "\n".join(result.alternatives[0].transcript for result in response.results)
    return transcript

def process_folder():
    for root, _, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith("wav"):
                input_path = os.path.join(root, file)

                # Get relative path and make mirrored output path
                rel_path = os.path.relpath(input_path, INPUT_DIR)
                rel_no_ext = os.path.splitext(rel_path)[0]
                output_path = os.path.join(OUTPUT_DIR, rel_no_ext + ".txt")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                try:
                    print(f"Processing: {input_path}")
                    converted_path = convert_audio(input_path)
                    transcript = transcribe_audio(converted_path)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(transcript)
                    os.remove(converted_path)  # Clean up temp file
                except Exception as e:
                    print(f"Error processing {input_path}: {e}")

process_folder()
