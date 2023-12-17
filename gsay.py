"""
Note: ssml must be well-formed according to:
    https://www.w3.org/TR/speech-synthesis/
"""
from enum import Enum
from pathlib import Path
import os
import argparse
import datetime
import shutil
import signal
import time
from glob import glob
import subprocess
import logging
from abc import ABC, abstractmethod

import yaml
from google.cloud import texttospeech
from google.auth.api_key import Credentials
from xdg_base_dirs import xdg_config_home

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")

id = get_timestamp()

# Paths
project_dir = Path(os.path.dirname(os.path.realpath(__file__)))
audio_dir = project_dir / 'audio_file_cache'

audio_dir.mkdir(exist_ok=True)

api_key_path = xdg_config_home() / "gsay" / 'api_key.yaml'
api_key = yaml.load(api_key_path.open(), Loader=yaml.FullLoader)

# Arguments
parser = argparse.ArgumentParser(description='Google Text to speech. Nightcored.')
parser.add_argument('--speed', type=float, help="Speed of the generated voice")
parser.add_argument('--pitch', type=float, help="Pitch of the generated voice")
parser.add_argument('--debug', action='store_true', help="Activate debug mode")
parser.add_argument('-o', '--output-file', type=Path, help="Output to this file instead of playing it.")
parser.add_argument('--ssml',  type=str, help='The next to speak as ssml annotated text.')
parser.add_argument('--speaker',  type=str, default="Alice", help='The speaker to use.')
parser.add_argument('text',  type=str, nargs='*', help='The next to speak.')

args = parser.parse_args()
args.text = " ".join(args.text)

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

class Speaker(ABC):
    def __init__(self):
        self.unique_name = None
        self.ff_rate_coef = None
        self.ff_tempo = None
        self.voice = None
        self.audio_config = None

    def speak(self, text=None, ssml=None):
        file_name = id

        audio_file = f"{audio_dir}/{file_name}.mp3"
        audio_file_pp = f"{audio_dir}/{file_name}_pp.mp3"

        client = texttospeech.TextToSpeechClient(credentials=Credentials(api_key))
        if text:
            synthesis_input = texttospeech.SynthesisInput(text=text)
        elif ssml:
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
        else:
            return

        logging.debug("Sending client synthesise speech request")
        response = client.synthesize_speech(
            input=synthesis_input, voice=self.voice, audio_config=self.audio_config)
        logging.debug("Received response")

        if not os.path.isdir(audio_dir):
            os.mkdir(audio_dir, )
        with open(audio_file, "wb") as out:
            out.write(response.audio_content)

        logging.debug("Applying nightcore with ffmpeg")
        os.system(f'ffmpeg -loglevel quiet -i "{audio_file}" '
            f'-filter:a "atempo={self.ff_tempo},asetrate=44100*{self.ff_rate_coef}" '
            f'"{audio_file_pp}" -y')
        os.remove(audio_file)

        if args.output_file is not None:
            shutil.move(audio_file_pp, args.output_file)
            return

        proc = None
        try:
            proc = subprocess.Popen(['mpv', '--really-quiet', audio_file_pp])
            signal.signal(signal.SIGTERM, lambda signum, frame: proc.terminate())
            proc.wait()
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
        except KeyboardInterrupt:
            if proc:
                proc.terminate()
        finally:
            if proc:
                proc.terminate()
            os.remove(audio_file_pp)

class Alice(Speaker):
    unique_name = "Alice"
    def __init__(self):
        self.ff_rate_coef = 1.08
        self.ff_tempo = 1.0
        self.voice = texttospeech.VoiceSelectionParams(
            name = "en-US-Wavenet-H",
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate = 1.4,
            pitch = 0.6,
            volume_gain_db = 0,
            sample_rate_hertz = 44100,
        )

class Mary(Speaker):
    unique_name = "Mary"
    def __init__(self):
        "ACF"
        self.ff_rate_coef = 1.185
        self.ff_tempo = 1.0
        self.voice = texttospeech.VoiceSelectionParams(
            name = "en-GB-Neural2-A",
            language_code="en-GB",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate = 1.2,
            pitch = 0.6,
            volume_gain_db = 1.5,
            sample_rate_hertz = 44100,
        )

class SpeakerEnum(Enum):
    ALICE = Alice
    MARY = Mary

def speak(msg: str, ssml: str = None, speaker: SpeakerEnum = SpeakerEnum.ALICE):
    speaker.value().speak(msg, ssml)

def main():
    speak(args.text, args.ssml, speaker=SpeakerEnum[args.speaker.upper()])