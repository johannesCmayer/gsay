"""
Note: ssml must be well-formed according to:
    https://www.w3.org/TR/speech-synthesis/
"""
from enum import Enum
from pathlib import Path
import os
import datetime
import shutil
import signal
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

class Speaker(ABC):
    def __init__(self, unique_name=None, ff_rate_coef=None, ff_tempo=None, voice=None, audio_config=None, output_file=None):
        self.unique_name = None
        self.ff_rate_coef = None
        self.ff_tempo = None
        self.voice = None
        self.audio_config = None
        self.output_file = None

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

        if self.output_file:
            shutil.move(audio_file_pp, self.output_file)
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

def speak(msg: str, ssml: str = None, speaker: SpeakerEnum = SpeakerEnum.ALICE, output_file=None):
    speaker_instance = speaker.value(output_file=output_file)
    speaker_instance.speak(msg, ssml)