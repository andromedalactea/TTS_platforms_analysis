import os
from google.cloud import texttospeech
# Set the environment variable for Google Cloud authentication credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/andromedalactea/test/google/stately-gist-381622-a8af890757d5.json"

def text_to_speech_api_google(text, audio_path, speed):
   
    # Create an instance of the Text-to-Speech client
    client = texttospeech.TextToSpeechClient()

    # Define the input text to be synthesized
    synthesis_input = texttospeech.SynthesisInput(ssml=text)
    # Configure the voice selection, including the language code and voice name
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Studio-O"  # Make sure this voice name is available in Google Cloud Text-to-Speech
    )

    # Configure the audio configuration parameters
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # Correct enum for WAV format
        effects_profile_id=["large-home-entertainment-class-device"],  # Audio effect profile
        pitch=0,  # Pitch
        speaking_rate=speed # Speaking rate
    )


    # Make the Text-to-Speech request with the selected parameters
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # The audio content of the response is binary
    with open(audio_path, "wb") as out:  # Change to output.wav since we are using LINEAR16 audio
        # Write the response to the output file
        out.write(response.audio_content)
if __name__ == "__main__":
    text_to_speech_api_google(
        """
        <speak>
        our new
        <break time="200ms"/> 
        and innovative technology
        </speak>
        """
        , "/home/andromedalactea/test/google/autput_audios/our_new_and_innovative_technology.wav", 1)