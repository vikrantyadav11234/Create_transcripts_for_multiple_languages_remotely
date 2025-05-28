import os
import io
import shutil
from pathlib import Path
from google.cloud import speech, storage
from pydub import AudioSegment

# Set your credentials path
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/vikrant/youtube_downloader/gstt_json.json"

BUCKET_NAME = "mixed_audio_data"
BASE_GCS_PATH = "full_audio/english"
LOCAL_TMP = "/tmp/gstt_work/english"
OUTPUT_DIR = "/home/vikrant/youtube_downloader/english_transcripts"

# Init GCP clients
speech_client = speech.SpeechClient()
storage_client = storage.Client()

os.makedirs(LOCAL_TMP, exist_ok=True)

def convert_mp3_to_wav(mp3_path, wav_path):
    sound = AudioSegment.from_file(mp3_path)
    sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    sound.export(wav_path, format="wav")
    return wav_path

def download_blob(bucket_name, source_blob_name, destination_file_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    return f"gs://{bucket_name}/{destination_blob_name}"

def transcribe_long_audio_gcs(gcs_uri):
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-IN",  # English (India)
        enable_automatic_punctuation=True
    )
    operation = speech_client.long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=5000)

    transcript = " ".join(result.alternatives[0].transcript for result in response.results)
    return transcript

def process_bucket():
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=BASE_GCS_PATH)
    blobs_list = list(blobs)

    if not blobs_list:
        print("No blobs found in the bucket.")
        return

    print(f"Found {len(blobs_list)} blobs to process.")

    for blob in blobs_list:
        if blob.name.endswith(".mp3"):
            try:
                rel_path = os.path.relpath(blob.name, BASE_GCS_PATH)
                base_name = os.path.splitext(rel_path)[0]
                local_out_path = os.path.join(OUTPUT_DIR, base_name + ".txt")

                # Skip if already processed
                if os.path.exists(local_out_path):
                    print(f"Skipping already processed file: {blob.name}")
                    continue

                print(f"Processing: {blob.name}")

                mp3_local = os.path.join(LOCAL_TMP, os.path.basename(blob.name))
                wav_local = mp3_local.replace(".mp3", ".wav")
                gcs_wav_path = f"gstt_temp/{Path(wav_local).name}"

                download_blob(BUCKET_NAME, blob.name, mp3_local)
                print(f"Downloaded {mp3_local}")

                convert_mp3_to_wav(mp3_local, wav_local)
                print(f"Converted to WAV: {wav_local}")

                gcs_uri = upload_blob(BUCKET_NAME, wav_local, gcs_wav_path)
                print(f"Uploaded WAV to GCS: {gcs_uri}")

                transcript = transcribe_long_audio_gcs(gcs_uri)
                print(f"Transcript: {transcript}")

                os.makedirs(os.path.dirname(local_out_path), exist_ok=True)
                with open(local_out_path, "w", encoding="utf-8") as f:
                    f.write(transcript)

                print(f"Transcript saved to {local_out_path}")

                # Cleanup
                os.remove(mp3_local)
                os.remove(wav_local)
                storage_client.bucket(BUCKET_NAME).blob(gcs_wav_path).delete()

            except Exception as e:
                print(f"Error processing {blob.name}: {e}")

process_bucket()
