import argparse
import logging
from pathlib import Path
from gsay.gsay import SpeakerEnum, speak
import sys
import portalocker

# Arguments
parser = argparse.ArgumentParser(description='Google Text to speech. Nightcored. By default stdin is only processed if neither `text` nor `--ssml` is provided.')
parser.add_argument('--stdin', action='store_true', help="Speak first command line args then stdin.")
parser.add_argument('--speed', type=float, help="Speed of the generated voice")
parser.add_argument('--pitch', type=float, help="Pitch of the generated voice")
parser.add_argument('--debug', action='store_true', help="Activate debug mode")
parser.add_argument('-o', '--output-file', type=Path, help="Output to this file instead of playing it.")
parser.add_argument('--ssml',  type=str, help='The next to speak as ssml annotated text.')
parser.add_argument('--speaker',  type=str, default="Alice", help='The speaker to use.')
parser.add_argument('-e', '--echo',  action='store_true', help='Print the input test to stdout.')
parser.add_argument('--log-level', default='WARNING', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    help='Set the logging level')
parser.add_argument('--disable-lock', action='store_true', help='Disable the lock that ensures that only one gsay program can speak.')
parser.add_argument('text',  type=str, nargs='*', help='The next to speak.')

args = parser.parse_args()

log_level = getattr(logging, args.log_level.upper(), None)
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

args = parser.parse_args()
args.text = " ".join(args.text)

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

# USE PORTALOCKERichat

def main():
    # If we don't get any other input try to process stdin
    if args.disable_lock:
        dispatch()
    else:
        with open('/tmp/gsay_speak_lock', 'a+') as file:
            portalocker.lock(file, portalocker.LOCK_EX)
            dispatch()
            portalocker.unlock(file)

def dispatch():
    if not (args.text or args.ssml):
        process_stream()
    else:
        process_blob()
        if args.stdin:
            process_stream()

def process_stream():
    for line in sys.stdin:
        line = line.rstrip('\n')
        process_blob(line, "")

def process_blob(text=args.text, ssml=args.ssml, speaker=SpeakerEnum[args.speaker.upper()], output_file=args.output_file):
    if args.echo:
        if text:
            print(text)
        if ssml:
            print(ssml)
    speak(text, ssml, speaker, output_file)
