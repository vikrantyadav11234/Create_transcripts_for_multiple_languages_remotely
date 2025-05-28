import re
import os

def split_transcript(input_file, output_file):
    # Regular expression for splitting sentences based on punctuation
    sentence_endings = r"([।?!])"
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        text = infile.read()
    
    # Split the text based on sentence-ending punctuation
    sentences = re.split(sentence_endings, text)
    
    # Combine the sentence-ending punctuation with the sentence
    sentences = [sentences[i] + sentences[i+1] for i in range(0, len(sentences)-1, 2)]
    
    # Remove any empty sentences or unwanted spaces
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Save the sentences to a new file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for sentence in sentences:
            outfile.write(sentence + "\n")
    
    print(f"Transcript has been split and saved to {output_file}")

# Usage
def process_all_transcripts(transcript_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for transcript_file in os.listdir(transcript_dir):
        if transcript_file.endswith(".txt"):
            input_file = os.path.join(transcript_dir, transcript_file)
            output_file = os.path.join(output_dir, transcript_file)
            
            # Split the transcript and save the sentences
            split_transcript(input_file, output_file)

# Directories (modify these paths as needed)
TRANSCRIPT_DIR = "/home/vikrant/chunks_by_transcript/test_transcript"
OUTPUT_DIR = "/home/vikrant/chunks_by_transcript/split_transcripts"

process_all_transcripts(TRANSCRIPT_DIR, OUTPUT_DIR)
