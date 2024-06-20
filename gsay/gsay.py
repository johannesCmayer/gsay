"""
Note: ssml must be well-formed according to:
    https://www.w3.org/TR/speech-synthesis/
"""

#TODO: Have the cache also take into account how often a particular file has been retrieved from the cache when deleting files.
#TODO: Add cli flag that disables caching for the particular invocation.

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import os
import signal
from glob import glob
import subprocess
import logging
from abc import ABC, abstractmethod
from pathlib import Path
import tempfile
import logging
import hashlib
import os
from datetime import datetime

import yaml
from google.cloud import texttospeech
from google.auth.api_key import Credentials
from xdg_base_dirs import xdg_config_home, xdg_cache_home

audio_file_cache_dir = xdg_cache_home() / 'gsay'
# n most recently accessed files to keep in the audio-file cache.
cache_size = 1000

def play_audio_file(audio_file):
    proc = None

    try:
        proc = subprocess.Popen(['mpv', '--really-quiet', str(audio_file)])
        signal.signal(signal.SIGTERM, lambda signum, frame: proc.terminate())
        proc.wait()
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
    except KeyboardInterrupt:
        if proc:
            proc.terminate()
    finally:
        if proc:
            proc.terminate()

def seconds_since_last_access(path : Path):
    last_access_time = path.stat().st_atime
    last_access_datetime = datetime.fromtimestamp(last_access_time)
    current_datetime = datetime.now()
    time_difference = current_datetime - last_access_datetime
    seconds_since_list_access = time_difference.seconds
    return seconds_since_list_access

def get_file_content_hash(msg : str, speaker : str):
    return hashlib.sha256(f"{msg}{speaker}".encode()).hexdigest()

def calculate_cache_path(msg : str, speaker : str):
    return audio_file_cache_dir / f"{get_file_content_hash(msg, speaker)}.mp3"

def clean_cache():
    files = list(audio_file_cache_dir.iterdir())
    # Don't delete files from the past 2 days
    files = filter(lambda x: seconds_since_last_access(x) < 60*60*24*2, files)
    files = sorted(files, key=lambda x: seconds_since_last_access(x))
    i = 0
    for f in files[cache_size:]:
        f.unlink()
        i += 1
    logging.debug(f"Deleted {i} files from the cache.")

def fetch_audiofile_from_cache(msg : str, speaker : str) -> Path:
    cache_file = calculate_cache_path(msg, speaker)
    if cache_file.exists():
        logging.debug(f"Cache hit for speaker {speaker} saying \"{msg}\". Using {cache_file}")
        return cache_file
    else:
        return None
    
class Speaker(ABC):
    def __init__(self, api_key, unique_name=None, ff_rate_coef=1, ff_tempo=1, voice=None, audio_config=None, output_file=None):
        self.api_key = api_key
        self.unique_name = unique_name
        self.ff_rate_coef = ff_rate_coef
        self.ff_tempo = ff_tempo
        self.voice = voice
        self.audio_config = audio_config
        self.output_file = output_file

    def _generate_audio_file(self, text, ssml, target_file_path : Path):
        logging.debug(f"Generating new audio file.")

        with tempfile.NamedTemporaryFile() as audio_file:
            client = texttospeech.TextToSpeechClient(credentials=Credentials(self.api_key))
            if text:
                synthesis_input = texttospeech.SynthesisInput(text=text)
            elif ssml:
                synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
            else:
                raise Exception("Both text and ssml are None.")

            logging.debug("Sending client synthesise speech request")
            response = client.synthesize_speech(
                input=synthesis_input, voice=self.voice, audio_config=self.audio_config)
            logging.debug("Received response")

            audio_file.write(response.audio_content)

            logging.debug("Applying nightcore with ffmpeg")
            os.system(f'ffmpeg -loglevel quiet -i "{audio_file.name}" '
                f'-filter:a "atempo={self.ff_tempo},asetrate=44100*{self.ff_rate_coef}" '
                f'"{target_file_path}" -y')

        return target_file_path

    def get_audio_file(self, text=None, ssml=None):
        is_text = ssml == None

        audio_file = fetch_audiofile_from_cache(text, speaker=self.unique_name)
        # Generate and immediately cache the file if it does not exist
        if not audio_file:
            clean_cache()
            audio_file_cache_dir.mkdir(exist_ok=True)
            cache_file = calculate_cache_path(text if is_text else ssml, self.unique_name)
            audio_file = self._generate_audio_file(text, ssml, cache_file)
        
        return audio_file

    def speak(self, text=None, ssml=None):
        audio_file = self.get_audio_file(text, ssml)

        if self.output_file:
            self.output_file.write_bytes(audio_file.read_bytes())
            return
        else:
            play_audio_file(audio_file)


class Alice(Speaker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unique_name = "Alice"
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unique_name = "Mary"
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

# @dataclass
# class SpeakerConfig:
#     unique_name : str
#     ff_rate_coef : float
#     ff_tempo : float
#     voice : texttospeech.VoiceSelectionParams
#     audio_config : texttospeech.AudioConfig


class SpeakerEnum(Enum):
    ALICE = Alice
    MARY = Mary

def speak(msg: str, ssml: str = None, speaker: SpeakerEnum = SpeakerEnum.ALICE, output_file=None):
    # Paths
    api_key_path = xdg_config_home() / "gsay" / 'api_key.yaml'
    api_key = yaml.load(api_key_path.open(), Loader=yaml.FullLoader)

    speaker_instance = speaker.value(api_key, output_file=output_file)
    speaker_instance.speak(msg, ssml)