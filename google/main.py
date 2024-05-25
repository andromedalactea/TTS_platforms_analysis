import os
from google.cloud import texttospeech, speech

# Configurate the environment variable for Google Cloud authentication credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/andromedalactea/test/google/vaulted-bit-390622-5ede8f5d79ee.json"

from join_audios import merge_audios_with_pause

def synthesize_text(text, file_path, add_breaks=False, speed=1.0, language_code="en-US", voice_name="en-US-Polyglot-1"):
    """Función para sintetizar texto a audio con la opción de agregar pausas entre palabras o no."""
    client = texttospeech.TextToSpeechClient()
    # Check if we need to add breaks between words
    if add_breaks:
        words = text.split()
        break_tag = ' <break time="1ms"/> '
        text = "<speak>" + break_tag.join(words) + "</speak>"
        print(text)
        synthesis_input = texttospeech.SynthesisInput(ssml=text)
    else:
        synthesis_input = texttospeech.SynthesisInput(text=text)
    
    
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=speed
    )
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    
    # Save the audio content to a file
    with open(file_path, "wb") as out:
        out.write(response.audio_content)

def split_audio(input_audio_path, output_folder, response, identification_group = ""):
    """Function to split the audio file into individual words."""
    import wave
    import audioop
    from contextlib import closing

    with wave.open(input_audio_path, "rb") as in_wav:
        frame_rate = in_wav.getframerate()
        channels = in_wav.getnchannels()
        width = in_wav.getsampwidth()

        for index, result in enumerate(response.results):
            index = 0
            for word_info in result.alternatives[0].words:
                word = word_info.word
                start = int(word_info.start_time.total_seconds() * frame_rate)
                end = int(word_info.end_time.total_seconds() * frame_rate)
                in_wav.setpos(start)
                frame_data = in_wav.readframes(end - start)
                # Crear archivo de audio para cada palabra
                with wave.open(os.path.join(output_folder, f"{index}_{identification_group}_{word}.wav"), "wb") as out_wav:
                    out_wav.setnchannels(channels)
                    out_wav.setsampwidth(width)
                    out_wav.setframerate(frame_rate)
                    out_wav.writeframes(frame_data)
                index += 1



def transcribe_file(speech_file, language_code="en-US"):
    """Function to transcribe the given audio file."""
    client = speech.SpeechClient()
    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
        language_code=language_code,
        enable_word_time_offsets=True
    )

    

    return client.recognize(config=config, audio=audio)

def generate_audio_samples(text, output_dir, language_code="en-US", voice_name="en-US-Polyglot-1"):
    """Main function to generate audio samples."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "word_by_word"), exist_ok=True)
    
    # Audio without pauses
    synthesize_text(text, os.path.join(output_dir, "1__full_normal_audio_TTS_google_STT_NotRequire.wav"), add_breaks=False, language_code=language_code, voice_name=voice_name)
    
    # Audio with pauses between words
    synthesize_text(text, os.path.join(output_dir, "2__spaced_audio_SSSML_breaktimes_TTS_google_STT_NotRequire.wav"), add_breaks=True, language_code=language_code, voice_name=voice_name)
    
    # Transcription of the audio files
    response = transcribe_file(os.path.join(output_dir, "2__spaced_audio_SSSML_breaktimes_TTS_google_STT_NotRequire.wav"), language_code=language_code)
    print(os.path.join(output_dir, "word_by_word"))
    split_audio(os.path.join(output_dir, "2__spaced_audio_SSSML_breaktimes_TTS_google_STT_NotRequire.wav"), os.path.join(output_dir, "word_by_word"), response, identification_group="spaced")

    # Transcription of the audio files
    response = transcribe_file(os.path.join(output_dir, "1__full_normal_audio_TTS_google_STT_NotRequire.wav"), language_code=language_code)
    split_audio(os.path.join(output_dir, "1__full_normal_audio_TTS_google_STT_NotRequire.wav"), os.path.join(output_dir, "word_by_word"), response, identification_group="full")

    # Generate an audio with the words spaced in only one
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'spaced', os.path.join(output_dir, "4__Joined_spaced_audio_with_spaced_SSML_wordsTTS_google_STT_google.wav"))
    
    # Generate an audio with the words spaced in only one for full spaced audio
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'full', os.path.join(output_dir, "3__Joined_spaced_audio_with_full_words_TTS_google_STT_google.wav"))

# Example Usage
if __name__ == '__main__':
    list_exmaples = ["Les enfants ont appris à lire rapidement", "Mon ancien ami est venu me rendre visite hier"]
    for text in list_exmaples:
        output_dir = "/home/andromedalactea/test/google/autput_audios"
        # Generar una nueva carpeta para cada ejecución
        output_dir = os.path.join(output_dir, text.replace(" ", "_"))

        generate_audio_samples(text, output_dir, language_code="fr-FR", voice_name="fr-FR-Studio-D")

# ["Les enfants ont appris à lire rapidement", "Mon ancien ami est venu me rendre visite hier"] language_code="fr-FR", voice_name="fr-FR-Studio-D"
# ["Our New an innovative technology", "Is it ready?", "What are you doing?"] language_code="en-US", voice_name="en-US-Studio-Q"
# ["Le he dicho", "Si así es", "Te espero", "Voy a ir"] language_code="es-US", voice_name="es-US-Studio-B"