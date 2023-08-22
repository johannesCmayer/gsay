"""Synthesizes speech from the input string of text or ssml.
Make sure to be working in a virtual environment.

Note: ssml must be well-formed according to:
    https://www.w3.org/TR/speech-synthesis/
"""
from pathlib import Path
import os
import argparse
import datetime
import shutil
import time
from glob import glob

import yaml
import click
from google.cloud import texttospeech
from google.auth.api_key import Credentials

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")

id = get_timestamp()

# Paths
project_dir = Path(os.path.dirname(os.path.realpath(__file__)))
audio_dir = project_dir / 'audio_file_cache'
locks_dir = project_dir / 'locks'
lock_file = locks_dir / id

audio_dir.mkdir(exist_ok=True)
locks_dir.mkdir(exist_ok=True)

api_key = yaml.load(open(project_dir / 'api_key.yaml', 'r'), Loader=yaml.FullLoader)


# Arguments
parser = argparse.ArgumentParser(description='Google Text to speech. Nightcored.')
parser.add_argument('--speed', type=float, help="Speed of the generated voice")
parser.add_argument('--pitch', type=float, help="Pitch of the generated voice")
parser.add_argument('--clear-locks', action='store_true', help="Clear all the locks.")
parser.add_argument('--debug', action='store_true', help="Activate debug mode")
parser.add_argument('-o', '--output-file', type=Path, help="Output to this file instead of playing it.")
parser.add_argument('text',  type=str, nargs='*', help='sum the integers (default: find the max)')

args = parser.parse_args()
args.text = " ".join(args.text)

if args.clear_locks:
    for f in locks_dir.iterdir():
        f.unlink()
    exit(0)

if args.text == "":
    raise ValueError("No text to speak was provided.")

female_wavenet_voices_us = [f"en-US-Wavenet-{voice}" for voice in ["C","E","F","G","H"]]
female_standard_voices_us = [f"en-US-Standard-{voice}" for voice in ["F"]]

def debug_notify(msg):
    if args.debug:
        os.system(f"notify-send '{msg}'")

def wait_for_lock():
    for lock in wait_locks:
        if lock.name == lock_file.name:
            continue
        while lock.is_file():
            time.sleep(0.005)

class Speaker:
    def __init__(self):
        pass

    def speak(self, text=None, ssml=None):
        if ssml is not None:
            raise NotImplemented()
        #ssml = '<prosody rate="slow" pitch="2st">Can you hear me now? Yes, that is right! I am here.</prosody>'

        file_name = id

        audio_file = f"{audio_dir}/{file_name}.mp3"
        audio_file_pp = f"{audio_dir}/{file_name}_pp.mp3"

        client = texttospeech.TextToSpeechClient(credentials=Credentials(api_key))
        synthesis_input = texttospeech.SynthesisInput(text=text)

        response = client.synthesize_speech(
            input=synthesis_input, voice=self.voice, audio_config=self.audio_config
        )

        if not os.path.isdir(audio_dir):
            os.mkdir(audio_dir, )
        with open(audio_file, "wb") as out:
            out.write(response.audio_content)

        os.system(f'ffmpeg -loglevel quiet -i "{audio_file}" '
            f'-filter:a "atempo={self.ff_tempo},asetrate=44100*{self.ff_rate_coef}" '
            f'"{audio_file_pp}" -y')
        os.remove(audio_file)

        if args.output_file is not None:
            lock_file.unlink()
            shutil.move(audio_file_pp, args.output_file)
            return
        
        wait_for_lock()

        # We calculate a speedup factor based on the number of sheduled files
        # We want to catch up if there are many files sheduled for speaking.
        MAX_SPEED = 1.3
        MIN_SPEED = 1.0
        UPPER_RANGE = 3

        speed_coef = MIN_SPEED + (len(list(locks_dir.iterdir())) - 1) / UPPER_RANGE * (MAX_SPEED - MIN_SPEED)
        speed_coef = min(MAX_SPEED, max(MIN_SPEED, speed_coef))
        debug_notify(f"speedup: {speed_coef}")

        os.system(f'mpv --speed={speed_coef} --no-resume-playback "{audio_file_pp}"')
        lock_file.unlink()
        os.remove(audio_file_pp)


class Alice(Speaker):
    def __init__(self):
        self.unique_name = "Alice"
        self.ff_rate_coef = 1.05
        self.ff_tempo = 1.0
        self.voice = texttospeech.VoiceSelectionParams(
            name = "en-US-Wavenet-H",
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate = 1.4 * speak_rate,
            pitch = 0.6,
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
            speaking_rate = 0.8 * speak_rate,
            pitch = 1,
            volume_gain_db = 0,
            sample_rate_hertz = 44100,
            #"effectsProfileId": [
            #    string
            #]
        )

def main():
    speaker = Alice()
    speaker.speak(args.text)

wait_locks = list(locks_dir.iterdir())
lock_file.touch()

pitch_coef = args.pitch if args.pitch else 1
speak_rate = args.speed if args.speed else 1

if __name__ == "__main__":
    try:
        main()
    finally:
        if lock_file.is_file():
            lock_file.unlink()
