import os
from dotenv import load_dotenv
import requests
import json
import wave
import audioop
from contextlib import closing

# Load environment variables
load_dotenv(override=True)

from join_audios import merge_audios_with_pause

# Function to get an environment variable or raise an error if not set
def get_env_variable(name):
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable '{name}' is not set.")
    return value

# Function to get an access token
def get_access_token(subscription_key, region):
    fetch_token_url = f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key
    }
    response = requests.post(fetch_token_url, headers=headers)
    response.raise_for_status()
    return response.text

# Function to perform TTS using Azure Cognitive Services
def synthesize_text(text, file_path, voice_name="en-US-ChristopherNeural", language_code="en-US", add_breaks=False):
    access_token = get_access_token(os.environ.get('SPEECH_KEY'), os.environ.get('SPEECH_REGION'))
    url = f"https://{os.environ.get('SPEECH_REGION')}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'riff-16khz-16bit-mono-pcm',
        'User-Agent': 'YOUR_APPLICATION_NAME'
    }
    
    if add_breaks:
        words = text.split()
        break_tag = ' <break time="500ms"/> '
        text = break_tag.join(words) 
    
    ssml = f"""
    <speak version='1.0' xml:lang='{language_code}'>
        <voice xml:lang='{language_code}' xml:gender='Male' name='{voice_name}'>
            {text}
        </voice>
    </speak>
    """
    
    response = requests.post(url, headers=headers, data=ssml)
    response.raise_for_status()
    
    with open(file_path, "wb") as out:
        out.write(response.content)
    print(f"Text-to-speech completed and saved to {file_path}")

# Function to transcribe an audio file
def transcribe_audio_file(audio_file_path, language_code="en-US"):
    subscription_key = os.environ.get('SPEECH_KEY')
    region = os.environ.get('SPEECH_REGION')

    url = f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    params = {
        'language': language_code,
        'format': 'detailed',
        'wordLevelTimestamps': True
    }
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-Type': 'audio/wav'
    }

    with open(audio_file_path, 'rb') as audio_file:
        response = requests.post(url, params=params, headers=headers, data=audio_file)
        response.raise_for_status()
        return response.json()

# Function to split audio based on transcription response
def split_audio(input_audio_path, output_folder, response, identification_group=""):
    with wave.open(input_audio_path, "rb") as in_wav:
        frame_rate = in_wav.getframerate()
        channels = in_wav.getnchannels()
        width = in_wav.getsampwidth()

        for index, result in enumerate(response["NBest"][0]["Words"]):
            word = result["Word"]
            start = int(result["Offset"] / 10000000 * frame_rate)
            duration = int(result["Duration"] / 10000000 * frame_rate)
            end = start + duration
            in_wav.setpos(start)
            frame_data = in_wav.readframes(end - start)
            with wave.open(os.path.join(output_folder, f"{index}_{identification_group}_{word}.wav"), "wb") as out_wav:
                out_wav.setnchannels(channels)
                out_wav.setsampwidth(width)
                out_wav.setframerate(frame_rate)
                out_wav.writeframes(frame_data)

# Main function to generate audio samples
def generate_audio_samples(text, output_dir, language_code="en-US", voice_name="en-US-ChristopherNeural"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "word_by_word"), exist_ok=True)
    
    # Generate audio without pauses
    synthesize_text(text, os.path.join(output_dir, "1__full_normal_audio_TTS_azure_STT_NotRequire.wav"), language_code=language_code, voice_name=voice_name, add_breaks=False)
    
    # Generate audio with pauses between words
    synthesize_text(text, os.path.join(output_dir, "2__spaced_audio_SSML_breaktimes_TTS_azure_STT_NotRequire.wav"), language_code=language_code, voice_name=voice_name, add_breaks=True)
    
    # Transcribe and extract individual audios
    response = transcribe_audio_file(os.path.join(output_dir, "2__spaced_audio_SSML_breaktimes_TTS_azure_STT_NotRequire.wav"), language_code=language_code)
    split_audio(os.path.join(output_dir, "2__spaced_audio_SSML_breaktimes_TTS_azure_STT_NotRequire.wav"), os.path.join(output_dir, "word_by_word"), response, identification_group="spaced")

    response = transcribe_audio_file(os.path.join(output_dir, "1__full_normal_audio_TTS_azure_STT_NotRequire.wav"), language_code=language_code)
    split_audio(os.path.join(output_dir, "1__full_normal_audio_TTS_azure_STT_NotRequire.wav"), os.path.join(output_dir, "word_by_word"), response, identification_group="full")

    # Generate an audio with the words spaced in only one
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'spaced', os.path.join(output_dir, "4__Joined_spaced_audio_with_spaced_SSML_wordsTTS_Azure_STT_Azure.wav"))
    
    # Generate an audio with the words spaced in only one for full spaced audio
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'full', os.path.join(output_dir, "3__Joined_spaced_audio_with_full_words_TTS_Azure_STT_Azure.wav"))

# Example usage
if __name__ == '__main__':
    list_examples = ["Our New and innovative technology", "Is it ready?", "What are you doing?"]

    for text in list_examples:
        output_dir = "/home/andromedalactea/test/tts_analysis/azure_microsoft/autput_audios"
        output_dir = os.path.join(output_dir, text.replace(" ", "_"))
        generate_audio_samples(text, output_dir, language_code="en-US", voice_name="en-US-AndrewMultilingualNeural")

# ["Les enfants ont appris à lire rapidement", "Mon ancien ami est venu me rendre visite hier"] language_code="fr-FR", voice_name="fr-FR-HenriNeural"
# ["Our New an innovative technology", "Is it ready?", "What are you doing?"] language_code="en-US", voice_name="en-US-Studio-Q"
# ["Le he dicho", "Si es así", "Te espero", "Voy a ir"] language_code="es-US", voice_name="es-US-AlonsoNeural"
