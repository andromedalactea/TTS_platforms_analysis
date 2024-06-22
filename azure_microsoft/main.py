import os
import re
from dotenv import load_dotenv
import requests
import json
import wave
import audioop
from contextlib import closing
import azure.cognitiveservices.speech as speechsdk

# Load environment variables
load_dotenv(override=True)

from join_audios import merge_audios_with_pause

def create_ssml(text, language_code, voice_name, ssml_rate=100, ssml_break=0):
    """Function to create SSML text with the provided rate and break time."""
    ssml_prefix = f"""<speak version='1.0' xml:lang='{language_code}'>
        <voice xml:lang='{language_code}' xml:gender='Male' name='{voice_name}'>"""
    ssml_suffix = '</voice></speak>'

    break_tag = ''

    break_tag = f' <break time="{ssml_break}ms"/> '

    phrases = []
    mark_counter = 0

    for phrase in text.split('. '):
        words = []
        for m in re.finditer(r'\S+', phrase):
            word = m.group()
            mark = f" <bookmark mark='{mark_counter}'/> "
            words.append(f'{mark}{word}')
            mark_counter += 1
        phrases.append(f'{break_tag}'.join(words))  # Añadir break entre palabras

    ssml_text = f'. {break_tag}'.join(phrases)  # Añadir break entre frases
    ssml_text = f'{ssml_prefix}{ssml_text}{ssml_suffix}'
    print(ssml_text)
    return ssml_text

def speech_synthesizer_bookmark_reached_cb(evt: speechsdk.SessionEventArgs):
    with open('azure_microsoft/audio_info.jsonl', 'a') as f:
        f.write(json.dumps({
            'AudioOffset': (evt.audio_offset) / 1e7,  # Convert to seconds
        }) + "\n")

        

# Function to perform TTS using Azure Cognitive Services
def synthesize_text(text, file_path, voice_name="en-US-ChristopherNeural", language_code="en-US", add_breaks=False):
    # Clean the audio_info.jsonl file
    with open('azure_microsoft/audio_info.jsonl', 'w') as f:
        pass

    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))

    # Required for WordBoundary event sentences.
    speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestSentenceBoundary, value='true')

    audio_config = speechsdk.audio.AudioOutputConfig(filename=file_path)
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    speech_synthesizer.bookmark_reached.connect(speech_synthesizer_bookmark_reached_cb)

    # Generate SSML text
    if add_breaks:
        ssml = create_ssml(text, language_code, voice_name, ssml_rate=100, ssml_break=50)
    else:
        ssml = create_ssml(text, language_code, voice_name, ssml_rate=100, ssml_break=0)

    speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml).get()
    
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Text-to-speech completed and saved to {file_path}")
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")

# Function to split audio based on transcription response
def split_audio(input_audio_path, output_folder, identification_group=""):
    with wave.open(input_audio_path, "rb") as in_wav:
        frame_rate = in_wav.getframerate()
        channels = in_wav.getnchannels()
        width = in_wav.getsampwidth()
        audio_length = in_wav.getnframes()

        list_audio_info = []
        with open('azure_microsoft/audio_info.jsonl', 'r') as file:
            for  line in file:
                list_audio_info.append(json.loads(line)['AudioOffset'])

        print(list_audio_info)
        for idx, audio_offset in enumerate(list_audio_info):   
            start = int(audio_offset * frame_rate)
            end = int(list_audio_info[idx + 1] * frame_rate) if idx + 1 < len(list_audio_info) else audio_length 
            
            print(f"Word {idx}: {start/frame_rate} - {end/frame_rate}")
            
            in_wav.setpos(start)
            frame_data = in_wav.readframes(end - start)

            with wave.open(os.path.join(output_folder, f"{idx}_{identification_group}_{idx}.wav"), "wb") as out_wav:
                out_wav.setnchannels(channels)
                out_wav.setsampwidth(width)
                out_wav.setframerate(frame_rate)
                out_wav.writeframes(frame_data)

                print(f"Saved {idx}_{identification_group}_{idx}.wav")

# Main function to generate audio samples
def generate_audio_samples(text, output_dir, language_code="en-US", voice_name="en-US-ChristopherNeural"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "word_by_word"), exist_ok=True)
    
    # Generate audio without pauses
    synthesize_text(text, os.path.join(output_dir, "1__full_normal_audio_TTS_azure.wav"), language_code=language_code, voice_name=voice_name, add_breaks=False)
    
    # Generate audio with pauses between words
    synthesize_text(text, os.path.join(output_dir, "2__spaced_audio_SSML_breaktimes_TTS_azure.wav"), language_code=language_code, voice_name=voice_name, add_breaks=True)
    
    # Transcribe and extract individual audios
    split_audio(os.path.join(output_dir, "2__spaced_audio_SSML_breaktimes_TTS_azure.wav"), os.path.join(output_dir, "word_by_word"), identification_group="spaced")
    split_audio(os.path.join(output_dir, "1__full_normal_audio_TTS_azure.wav"), os.path.join(output_dir, "word_by_word"), identification_group="full")

    # Generate an audio with the words spaced in only one
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'spaced', os.path.join(output_dir, "4__Joined_spaced_audio_with_spaced_SSML_wordsTTS.wav"))
    
    # Generate an audio with the words spaced in only one for full  audio
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'full', os.path.join(output_dir, "3__Joined_spaced_audio_with_full_words_TTS.wav"))

# Example usage
if __name__ == '__main__':
    list_examples = ["Les enfants ont appris à lire rapidement", "Mon ancien ami est venu me rendre visite hier"]

    for text in list_examples:
        output_dir = "/home/andromedalactea/freelance/TTS_platforms_analysis/azure_microsoft/autput_audios"
        output_dir = os.path.join(output_dir, text.replace(" ", "_"))
        generate_audio_samples(text, output_dir, language_code="fr-FR", voice_name="fr-FR-HenriNeural")

# ["Les enfants ont appris à lire rapidement", "Mon ancien ami est venu me rendre visite hier"] language_code="fr-FR", voice_name="fr-FR-HenriNeural"
# ["Our New an innovative technology", "Is it ready?", "What are you doing?"] language_code="en-US", voice_name="en-US-Studio-Q"
# ["Le he dicho", "Si es así", "Te espero", "Voy a ir"] language_code="es-US", voice_name="es-US-AlonsoNeural"