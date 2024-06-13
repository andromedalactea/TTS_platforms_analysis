import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/andromedalactea/test/tts_analysis/google/vaulted-bit-390622-5ede8f5d79ee.json"

import argparse

from google.cloud import speech

def transcribe_file(speech_file: str) -> speech.RecognizeResponse:
    """Transcribe the given audio file."""
    client = speech.SpeechClient()

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
        language_code="en-US",
        enable_word_time_offsets=True,
    )
    operation = client.long_running_recognize(config=config, audio=audio)

    response = operation.result(timeout=90)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:
        # The first alternative is the most likely one for this portion.
        print(f"Transcript: {result.alternatives[0].transcript}")

    return response


print(transcribe_file("/home/andromedalactea/test/tts_analysis/google/autput_audios/What_are_you_doing?/1__full_normal_audio_TTS_google_STT_NotRequire.wav"))