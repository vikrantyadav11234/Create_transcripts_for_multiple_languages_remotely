import os

# Function to split the transcript into chunks of N words
def split_transcript(input_file, output_file, words_per_line=20):
    # Open and read the input file
    with open(input_file, 'r', encoding='utf-8') as infile:
        text = infile.read()

    # Split the text into a list of words
    words = text.strip().split()
    
    # Break the list of words into lines with the specified number of words per line
    lines = [" ".join(words[i:i+words_per_line]) for i in range(0, len(words), words_per_line)]

    # Write the resulting lines into the output file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for line in lines:
            outfile.write(line + "\n")
    
    print(f"Transcript split into {len(lines)} lines and saved to {output_file}")

# Batch processor to process all transcript files in a directory
def process_all_transcripts(transcript_dir, output_dir, words_per_line=20):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Loop through all files in the transcript directory
    for transcript_file in os.listdir(transcript_dir):
        if transcript_file.endswith(".txt"):
            input_file = os.path.join(transcript_dir, transcript_file)
            output_file = os.path.join(output_dir, transcript_file)
            
            # Split the transcript and save the results
            split_transcript(input_file, output_file, words_per_line)

# ---- Set your directory paths here ----
TRANSCRIPT_DIR = "/home/vikrant/chunks_by_transcript/test_transcript"
OUTPUT_DIR = "/home/vikrant/chunks_by_transcript/split_transcripts"

# Process all the transcripts
process_all_transcripts(TRANSCRIPT_DIR, OUTPUT_DIR)
