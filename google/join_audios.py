import os
from pydub import AudioSegment

def merge_audios_with_pause(directory, keyword, output_file):
    """
    Merge audio files in the specified directory that contain the keyword in their names.
    The audios are sorted by the index in their names and combined with a 0.5 second pause between each.

    Args:
        directory (str): The directory to search for audio files.
        keyword (str): The keyword to filter audio files by.
        output_file (str): The path to save the combined audio file.

    Returns:
        None: Creates an output file with the merged audio.
    """
    # Create a list to store the audio segments
    audios = []
    
    # List all files in the directory
    for file in sorted(os.listdir(directory)):
        # Check if the file is a .wav and contains the keyword
        if file.endswith('.wav') and keyword in file.split('_')[1]:
            # Extract the index from the file name
            index = int(file.split('_')[0])
            # Load the audio file
            audio = AudioSegment.from_wav(os.path.join(directory, file))
            # Append a tuple of (index, audio) to the list
            audios.append((index, audio))
    
    # Sort the list by the index
    audios.sort()
    
    # Create an empty audio segment for combining
    combined = AudioSegment.silent(duration=0)  # Start with silence
    
    # Add 0.5 second of silence between audios
    pause = AudioSegment.silent(duration=1000)  # 500 ms = 0.5 second
    
    # Combine all the audios with the pause
    for _, audio in audios:
        combined += audio + pause
    
    # Export the combined audio to a file
    combined.export(output_file, format='wav')


# Exmaple Usage
if __name__ == '__main__':
    directory = '/home/andromedalactea/test/tts_analysis/google/autput_audios/Our_New_an_innovative_technology/word_by_word'
    merge_audios_with_pause(directory, 'spaced', '/home/andromedalactea/test/tts_analysis/google/autput_audios/Our_New_an_innovative_technology/output.wav')
