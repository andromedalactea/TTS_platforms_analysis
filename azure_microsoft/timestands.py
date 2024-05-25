import os
import requests
from dotenv import load_dotenv
import json
# Cargar las variables de entorno
load_dotenv(override=True)

# Función para obtener la variable de entorno o lanzar un error si no está configurada
def get_env_variable(name):
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable '{name}' is not set.")
    return value

def transcribe_audio_file(audio_file_path):
    # Obtener las variables de entorno
    subscription_key = get_env_variable('SPEECH_KEY')
    region = get_env_variable('SPEECH_REGION')

    # Definir la URL del servicio
    url = f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    params = {
        'language': 'en-US',
        'format': 'detailed',
        'wordLevelTimestamps': True
    }
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-Type': 'audio/wav'
    }

    # Leer el archivo de audio y realizar la solicitud HTTP POST
    with open(audio_file_path, 'rb') as audio_file:
        response = requests.post(url, params=params, headers=headers, data=audio_file)
        response.raise_for_status()  # Esto lanzará un error si la solicitud no es exitosa
        return response.json()

# Ruta del archivo de audio
audio_file_path = "/home/andromedalactea/test/tts_analysis/azure_microsoft/autput_audios/Our_New_and_innovative_technology/1__full_normal_audio_TTS_azure_STT_NotRequire.wav"

# Ejecutar la transcripción
try:
    result = transcribe_audio_file(audio_file_path)
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"An error occurred: {e}")
