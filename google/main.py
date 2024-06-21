import os
import re
from google.cloud import texttospeech_v1beta1 as texttospeech
from google.cloud import speech
from join_audios import merge_audios_with_pause

# Configurate the environment variable para Google Cloud authentication credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/andromedalactea/freelance/TTS_platforms_analysis/credentials/vaulted-bit-390622-5ede8f5d79ee.json"

def create_ssml(text, ssml_rate=100, ssml_break=0):
    """Function to create SSML text with the provided rate and break time."""
    ssml_prefix = '<speak>'
    ssml_suffix = '</speak>'

    break_tag = ''
    if ssml_break > 0:
        break_tag = f'<break time="{ssml_break}ms"/>'

    if ssml_rate != 100:
        ssml_prefix = ssml_prefix + f'<prosody rate="{ssml_rate}%">'
        ssml_suffix = '</prosody>' + ssml_suffix

    phrases = []
    mark_counter = 0

    for phrase in text.split('. '):
        words = []
        for m in re.finditer(r'\S+', phrase):
            word = m.group()
            mark = f'<mark name="{mark_counter}"/>'
            words.append(f'{mark}{word}')
            mark_counter += 1
        phrases.append(f'{break_tag}'.join(words))  # Añadir break entre palabras

    ssml_text = f'. {break_tag}'.join(phrases)  # Añadir break entre frases
    ssml_text = f'{ssml_prefix}{ssml_text}{ssml_suffix}'
    print(ssml_text)
    return ssml_text

def synthesize_text(text, file_path, add_breaks=False, speed=1.0, language_code="en-US", voice_name="en-US-Polyglot-1"):
    """Function to sintetize the text and save the audio file. Return the timepoints of the words."""
    client = texttospeech.TextToSpeechClient()
    
    if add_breaks:
        ssml_text = create_ssml(text, ssml_rate=int(speed * 100), ssml_break=10)
    else:
        ssml_text = create_ssml(text, ssml_rate=int(speed * 100))
    
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    )

    # Enable time point marking
    response = client.synthesize_speech(
        request=texttospeech.SynthesizeSpeechRequest(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
            enable_time_pointing=[texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
        )
    )
    
    # Save the audio content to a file
    with open(file_path, "wb") as out:
        out.write(response.audio_content)

    # Extract and return timepoints
    timepoints = response.timepoints
    word_timepoints = {int(tp.mark_name): tp.time_seconds for tp in timepoints}
    return word_timepoints

def split_audio(input_audio_path, output_folder, word_timepoints, identification_group=""):
    """Function to split the audio file into individual words based on provided timepoints."""
    import wave

    with wave.open(input_audio_path, "rb") as in_wav:
        frame_rate = in_wav.getframerate()
        channels = in_wav.getnchannels()
        width = in_wav.getsampwidth()
        audio_length = in_wav.getnframes()

        time_keys = sorted(word_timepoints.keys())
        print(f"Timepoints: {time_keys}")
        for idx in range(len(time_keys)):
            word_start = word_timepoints[time_keys[idx]]
            word_end = word_timepoints[time_keys[idx + 1]] if idx + 1 < len(time_keys) else audio_length / frame_rate
            print(f"Word {idx}: {word_start} - {word_end}")
            start_frame = int(word_start * frame_rate)
            end_frame = int(word_end * frame_rate)
            in_wav.setpos(start_frame)
            frame_data = in_wav.readframes(end_frame - start_frame)

            with wave.open(os.path.join(output_folder, f"{idx}_{identification_group}_{time_keys[idx]}.wav"), "wb") as out_wav:
                out_wav.setnchannels(channels)
                out_wav.setsampwidth(width)
                out_wav.setframerate(frame_rate)
                out_wav.writeframes(frame_data)

def generate_audio_samples(text, output_dir, language_code="en-US", voice_name="en-US-Polyglot-1"):
    """Main function to generate audio samples."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "word_by_word"), exist_ok=True)
    
    # Audio without pauses
    normal_audio_path = os.path.join(output_dir, "1__full_normal_audio_TTS_google_STT_NotRequire.wav")
    normal_timepoints = synthesize_text(text, normal_audio_path, add_breaks=False, language_code=language_code, voice_name=voice_name)
    
    # Audio with pauses between words
    spaced_audio_path = os.path.join(output_dir, "2__spaced_audio_SSSML_breaktimes_TTS_google_STT_NotRequire.wav")
    spaced_timepoints = synthesize_text(text, spaced_audio_path, add_breaks=True, language_code=language_code, voice_name=voice_name)
    
    # Split the audio files using the timepoints
    split_audio(spaced_audio_path, os.path.join(output_dir, "word_by_word"), spaced_timepoints, identification_group="spaced")
    split_audio(normal_audio_path, os.path.join(output_dir, "word_by_word"), normal_timepoints, identification_group="full")

    # Generate an audio with the words spaced in only one
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'spaced', os.path.join(output_dir, "4__Joined_spaced_audio_with_spaced_SSML_wordsTTS_google_STT_google.wav"))
    
    # Generate an audio with the words spaced in only one for full spaced audio
    merge_audios_with_pause(os.path.join(output_dir, "word_by_word"), 'full', os.path.join(output_dir, "3__Joined_spaced_audio_with_full_words_TTS_google_STT_google.wav"))

# Example Usage
if __name__ == '__main__':
    list_exmaples = ["Les enfants ont appris à lire rapidement", "Mon ancien ami est venu me rendre visite hier"]
    for text in list_exmaples:
        output_dir = "/home/andromedalactea/freelance/TTS_platforms_analysis/google/autput_audios"
        output_dir = os.path.join(output_dir, text.replace(" ", "_"))

        generate_audio_samples(text, output_dir, language_code="fr-FR", voice_name="fr-FR-Wavenet-A")


# ["Les enfants ont appris à lire rapidement", "Mon ancien ami est venu me rendre visite hier"] language_code="fr-FR", voice_name="fr-FR-Wavenet-A"
# ["Our New an innovative technology", "Is it ready?", "What are you doing?"] language_code="en-US", voice_name="en-US-Wavenet-B"
# ["Le he dicho", "Si así es", "Te espero", "Voy a ir"] language_code="es-US", voice_name="es-US-Wavenet-B"