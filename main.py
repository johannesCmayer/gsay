"""Synthesizes speech from the input string of text or ssml.
Make sure to be working in a virtual environment.

Note: ssml must be well-formed according to:
    https://www.w3.org/TR/speech-synthesis/
"""
from pathlib import Path
import os
import argparse
import click
from google.cloud import texttospeech


#parser = argparse.ArgumentParser(description='Process some integers.')
#parser.add_argument('text', const=sum, default="No text was given.",
#                    help='sum the integers (default: find the max)')


project_dir = os.path.dirname(os.path.realpath(__file__))
audio_cache_dir = f"{project_dir}/audio_file_cache"

# Build the voice request, select the language code ("en-US") and the ssml
# voice gender ("neutral")
# TODO use this
female_wavenet_voices_us = [f"en-US-Wavenet-{voice}" for voice in ["C","E","F","G","H"]]
female_standard_voices_us = [f"en-US-Standard-{voice}" for voice in ["F"]]
tempo = 1

class Speaker:
    def __init__(self):
        pass

    def speak(self, text=None, ssml=None):
        if ssml is not None:
            raise NotImplemented()
        #ssml = '<prosody rate="slow" pitch="2st">Can you hear me now? Yes, that is right! I am here.</prosody>'

        cache_dir = f"{audio_cache_dir}/{self.unique_name}"
        audio_file = f"{cache_dir}/{text}.mp3"
        audio_file_pp = f"{cache_dir}/{text}_pp.mp3"

        if not os.path.isfile(audio_file_pp):
            client = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            response = client.synthesize_speech(
                input=synthesis_input, voice=self.voice, audio_config=self.audio_config
            )

            Path(cache_dir).mkdir(parents=True, exist_ok=True)

            if not os.path.isdir(audio_cache_dir):
                os.mkdir(audio_cache_dir, )
            with open(audio_file, "wb") as out:
                out.write(response.audio_content)

            os.system(f'ffmpeg -loglevel quiet -i "{audio_file}" '
                f'-filter:a "atempo={self.ff_tempo},asetrate=44100*{self.ff_rate_coef}" '
                f'"{audio_file_pp}" -y')
            os.remove(audio_file)
        
        os.system(f'mpv --no-resume-playback "{audio_file_pp}" > /dev/null')


class Alice(Speaker):
    def __init__(self):
        self.unique_name = "Alice"
        self.ff_rate_coef = 1.20
        self.ff_tempo = 1.00
        self.voice = texttospeech.VoiceSelectionParams(
            name = "en-US-Wavenet-H",
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate = 0.8,
            pitch = 1,
            volume_gain_db = 0,
            sample_rate_hertz = 44100,
            #"effectsProfileId": [
            #    string
            #]
        )

class Test(Speaker):
    def __init__(self):
        self.ff_rate_coef = 1.20
        self.ff_tempo = 1.00
        self.voice = texttospeech.VoiceSelectionParams(
            name = "en-US-Wavenet-H",
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate = 0.8,
            pitch = 1,
            volume_gain_db = 0,
            sample_rate_hertz = 44100,
            #"effectsProfileId": [
            #    string
            #]
        )

@click.command()
@click.argument('text', type=click.STRING, nargs=-1)
def main(text):
    text = " ".join(text)

    speaker = Alice()
    speaker.speak(text)

if __name__ == "__main__":
    main()
