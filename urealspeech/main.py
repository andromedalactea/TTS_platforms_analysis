import os
from dotenv import load_dotenv
import requests
import wave
from pydub import AudioSegment
from unrealspeech import UnrealSpeechAPI,  save

# Load environment variables
load_dotenv(override=True)

from join_audios import merge_audios_with_pause

API_KEY = os.getenv('UNREALSPEECH_API_KEY')
speech_api = UnrealSpeechAPI(API_KEY)

# Function to perform TTS using Azure Cognitive Services
def synthesize_text(text, file_path, voice_name="Scarlett", language_code="en-US", add_breaks=False):
    # Clean the audio_info.jsonl file
    timestamp_type = "word"  # Choose from 'sentence' or 'word'
    bitrate = "192k"
    speed = 0
    pitch = 1.0

    # Perform the speech synthesis request
    response = speech_api.speech(
        text=text,
        voice_id=voice_name,
        bitrate=bitrate,
        timestamp_type=timestamp_type,
        speed=speed,
        pitch=pitch
    )

    save(response, file_path)

    # Extract the TimestampsUri
    timestamps_uri = response.get('TimestampsUri')

    # Download and print the JSON from the TimestampsUri
    if timestamps_uri:
        print(f"\nDownloading JSON from {timestamps_uri}...")
        json_response = requests.get(timestamps_uri)
        if (json_response.status_code == 200):
            timestamps = json_response.json()
            print("Timestamps JSON content:")
            print(timestamps)
        else:
            print(f"Failed to download JSON. Status code: {json_response.status_code}")
    else:
        print("No TimestampsUri found in the response.")

    return timestamps

# Function to convert MP3 to WAV
def convert_mp3_to_wav(mp3_path, wav_path):
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")
    # Remove the MP3 file after conversion
    os.remove(mp3_path)

# Function to split audio based on transcription response
def split_audio(timestands, input_audio_path, output_folder, identification_group=""):
    # Check if the file is MP3 and convert to WAV
    if input_audio_path.lower().endswith('.mp3'):
        wav_path = os.path.splitext(input_audio_path)[0] + '.wav'
        convert_mp3_to_wav(input_audio_path, wav_path)
        input_audio_path = wav_path

    with wave.open(input_audio_path, "rb") as in_wav:
        frame_rate = in_wav.getframerate()
        channels = in_wav.getnchannels()
        width = in_wav.getsampwidth()
        audio_length = in_wav.getnframes()

        for idx, audio_info in enumerate(timestands):
            word = audio_info['word']
            word_start = audio_info['start']
            word_end = audio_info['end']

            start = int(word_start * frame_rate)
            end = int(word_end * frame_rate)

            print(f"Word {idx}: {start/frame_rate} - {end/frame_rate}")

            in_wav.setpos(start)
            frame_data = in_wav.readframes(end - start)

            with wave.open(os.path.join(output_folder, f"{idx}_{identification_group}_{word}.wav"), "wb") as out_wav:
                out_wav.setnchannels(channels)
                out_wav.setsampwidth(width)
                out_wav.setframerate(frame_rate)
                out_wav.writeframes(frame_data)

                print(f"Saved {idx}_{identification_group}_{word}.wav")

# Main function to generate audio samples
def generate_audio_samples(text, output_dir, language_code="en-US", voice_name="en-US-ChristopherNeural"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "word_by_word"), exist_ok=True)

    # Generate audio without pauses
    timestands = synthesize_text(text, os.path.join(output_dir, "1__full_normal_audio_TTS_unrealspeech.mp3"), language_code=language_code, voice_name=voice_name, add_breaks=False)

    # Transcribe and extract individual audios
    split_audio(timestands, os.path.join(output_dir, "1__full_normal_audio_TTS_unrealspeech.mp3"), os.path.join(output_dir, "word_by_word"), identification_group="full")

    # Generate an audio with the words spaced in only one for full audio
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'full', os.path.join(output_dir, "3__Joined_spaced_audio_with_full_words_TTS_unrealspeech.wav"))

# Example usage
if __name__ == '__main__':
    list_examples = ["Our New an innovative technology", "Is it ready?", "What are you doing?"]

    for text in list_examples:
        output_dir = "/home/andromedalactea/freelance/TTS_platforms_analysis/urealspeech/output_audios"
        output_dir = os.path.join(output_dir, text.replace(" ", "_"))
        generate_audio_samples(text, output_dir, voice_name="Scarlett")
