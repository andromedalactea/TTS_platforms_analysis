import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Function to get environment variable or raise an error if not set
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
def text_to_speech(subscription_key, region, text):
    access_token = get_access_token(subscription_key, region)
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'riff-16khz-16bit-mono-pcm',
        'User-Agent': 'YOUR_APPLICATION_NAME'
    }
    ssml = f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice xml:lang='en-US' xml:gender='Male' name='en-US-ChristopherNeural'>
            {text}
        </voice>
    </speak>
    """
    response = requests.post(url, headers=headers, data=ssml)
    response.raise_for_status()
    return response.content

# Get text from the console and synthesize to the default speaker.
print("Enter some text that you want to speak >")
text = 'This is a test'
# Perform text-to-speech
try:
    subscription_key = get_env_variable('SPEECH_KEY')
    region = get_env_variable('SPEECH_REGION')
    audio_data = text_to_speech(subscription_key, region, text)
    
    # Save the audio to an MP3 file
    with open('/home/andromedalactea/test/tts_analysis/azure_microsoft/autput_audios/output.wav', 'wb') as audio_file:
        audio_file.write(audio_data)
    
    print("Text-to-speech completed and saved to output.mp3.")
except Exception as e:
    print(f"An error occurred: {e}")
