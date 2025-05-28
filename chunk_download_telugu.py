import os  
import subprocess  
import time  
from pydub import AudioSegment  
  
# ==================== PLACE YOUR YOUTUBE URLS HERE ====================  
urls = [ 
    "https://www.youtube.com/watch?v=OC6Ge903e7M",  
    "https://www.youtube.com/watch?v=L9NP7ORoRvs",  
    "https://www.youtube.com/watch?v=9VfYQ06mPLg",
    "https://www.youtube.com/watch?v=yvPQ4t0Bydc",
    "https://www.youtube.com/watch?v=gVpMYaJK9j4",
    "https://www.youtube.com/watch?v=PISGI3wXUgE",
    "https://www.youtube.com/watch?v=Sr57PVGZYaQ",
    "https://www.youtube.com/watch?v=RHrIQg79Beg",
    "https://www.youtube.com/watch?v=9FROfvj1oCg",
    "https://www.youtube.com/watch?v=5bqBre9wOLA",
    "https://www.youtube.com/watch?v=B30KvHixUmY",
    "https://www.youtube.com/watch?v=Ze2yAXInJXI",
    "https://www.youtube.com/watch?v=DUJj9qt9R14",
    "https://www.youtube.com/watch?v=D-liJoIyiaM",
    "https://www.youtube.com/watch?v=eic36tvDTvQ",
    "https://www.youtube.com/watch?v=-34qT-i_-34",
    "https://www.youtube.com/watch?v=0gjDCmTX8Pg",
    "https://www.youtube.com/watch?v=D23atk_QvMg",
    "https://www.youtube.com/watch?v=flI-QHVt6Vg",
    "https://www.youtube.com/watch?v=9qyFub2aU2U",
    "https://www.youtube.com/watch?v=YfZROm9Njig",
    "https://www.youtube.com/watch?v=s47pa492X8c",
    "https://www.youtube.com/watch?v=yqasOkf3joo",
    "https://www.youtube.com/watch?v=hkc8JGVzfnQ",
    "https://www.youtube.com/watch?v=PLH2e9wltNc",
    "https://www.youtube.com/watch?v=Zp3kIwJKQ1g",
    "https://www.youtube.com/watch?v=KnXC6j-B61g",
    "https://www.youtube.com/watch?v=E8mD31r9QKE",
    "https://www.youtube.com/watch?v=-EulbTIQheI",
    "https://www.youtube.com/watch?v=TCcej2e10vw"
    

]  
  
# Folder to save audio and chunks  
download_folder = "downloads_tam"  
chunk_output_base = "/home/vikrant/youtube_downloader/audio_chunks"  
language = "tam"  # Set to "tel" for Telugu  
  
# Create necessary folders  
os.makedirs(download_folder, exist_ok=True)  
os.makedirs(os.path.join(chunk_output_base, language), exist_ok=True)  
  
def download_audio(url):  
    """  
    Uses yt-dlp to download the best audio and convert it to mp3.  
    Returns path to the mp3 file and the video_id.  
    """  
    print(f"Downloading audio from: {url}")  
    try:  
        # Extract video ID  
        video_id = url.split("v=")[-1].split("&")[0]  
        mp3_filename = f"{video_id}.mp3"  
        mp3_path = os.path.join(download_folder, mp3_filename)  
          
        if os.path.exists(mp3_path):  
            print(f"Already downloaded: {mp3_path}")  
            return mp3_path, video_id  
        cmd = [  
            "yt-dlp",
            "--cookies", "/home/vikrant/youtube_downloader/cookies.txtD:\Models\audio_data_processing\cookies.txt",  # <-- USE EXPORTED COOKIES HERE
            "--no-playlist",
            "-x", "--audio-format", "mp3",  
            "-o", os.path.join(download_folder, f"{video_id}.%(ext)s"),  
            url  
        ]


 
        # # Download best audio and convert to mp3  
        # cmd = [  
        #     "yt-dlp",  
        #     "-x", "--audio-format", "mp3",  
        #     "-o", os.path.join(download_folder, f"{video_id}.%(ext)s"),  
        #     url  
        # ]  
        subprocess.run(cmd, check=True)  
        print(f"Downloaded: {mp3_path}")  
        return mp3_path, video_id  
  
    except subprocess.CalledProcessError as e:  
        print(f"Download failed for {url}: {e}")  
        return None, None  
  
def split_audio(file_path, video_id, chunk_duration=10000):  
    """  
    Splits the audio into 5-second chunks and saves them as .wav files.  
    """  
    print(f"Splitting audio: {file_path}")  
    try:  
        audio = AudioSegment.from_file(file_path)  
        output_folder = os.path.join(chunk_output_base, language)  
        audio_length = len(audio)  
  
        for start in range(0, audio_length, chunk_duration):  
            chunk = audio[start : start + chunk_duration]  
            start_str = "{:07.3f}".format(start / 1000.0)  
            end_str = "{:07.3f}".format(min((start + chunk_duration) / 1000.0, audio_length / 1000.0))  
            filename = f"{video_id}---{start_str}-{end_str}.wav"  
            chunk_path = os.path.join(output_folder, filename)  
              
            chunk.export(chunk_path, format="wav")  
            print("Chunk saved:", chunk_path)  
    except Exception as e:  
        print(f"Error splitting {file_path}: {e}")  
  
def process_all(urls):  
    """  
    Processes all URLs: downloads audio and splits it into chunks.  
    """  
    for url in urls:  
        print("=" * 60)  
        print(f"Processing URL: {url}")  
        try:  
            mp3_file, video_id = download_audio(url)  
            if mp3_file and video_id:  
                split_audio(mp3_file, video_id)  
        except Exception as e:  
            print(f"Error processing {url}: {e}")  
        print(f"Finished processing {url}\n")  
        time.sleep(30)  # Delay to avoid triggering rate limits  
  
# Run the script  
if __name__ == "__main__":  
    process_all(urls)  
    print("All URLs processed.")  