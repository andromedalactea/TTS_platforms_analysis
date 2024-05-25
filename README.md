# TTS Platform Analysis

This repository is designed to analyze various Text-to-Speech (TTS) platforms by generating audio samples in different formats. Each platform has its own directory and a `main.py` file that contains the main logic for processing and generating the audio files.


## Main Script Overview

Each `main.py` script in the platform directories follows a similar structure, performing the following tasks:

1. **Synthesizing Text to Audio**: Converts text to speech using the respective TTS service.
2. **Adding Breaks in Audio**: Optionally adds SSML (Speech Synthesis Markup Language) breaks between words.
3. **Transcribing Audio**: Converts audio back to text to obtain timestamps for each word.
4. **Splitting Audio**: Splits the synthesized audio into individual word files based on the transcribed timestamps.
5. **Merging Audios**: Merges individual word audio files into a single audio file with optional pauses between words.

## Generated Audio Formats

The repository generates four types of audio files for each input text:

1. **Original**: No SSML, no spaces between words.
2. **SSML**: Minimum SSML breaks, no spaces between words.
3. **Original_Spaced**: No SSML, 500ms spaces between words using timestamps.
4. **SSML_Spaced**: Minimum SSML breaks, 500ms spaces between words.

## Supported Languages and Voices

The scripts generate audio samples in various languages and voices as per the platform's capabilities.

Languages: English (US), Spanish,  French
