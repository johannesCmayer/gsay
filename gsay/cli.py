import argparse
import logging
from pathlib import Path
from gsay.gsay import SpeakerEnum, speak

# Arguments
parser = argparse.ArgumentParser(description='Google Text to speech. Nightcored.')
parser.add_argument('--speed', type=float, help="Speed of the generated voice")
parser.add_argument('--pitch', type=float, help="Pitch of the generated voice")
parser.add_argument('--debug', action='store_true', help="Activate debug mode")
parser.add_argument('-o', '--output-file', type=Path, help="Output to this file instead of playing it.")
parser.add_argument('--ssml',  type=str, help='The next to speak as ssml annotated text.')
parser.add_argument('--speaker',  type=str, default="Alice", help='The speaker to use.')
parser.add_argument('text',  type=str, nargs='*', help='The next to speak.')
parser.add_argument('-e', '--echo',  action='store_true', help='Print the input test to stdout.')

args = parser.parse_args()
args.text = " ".join(args.text)

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

def main():
    if args.echo:
        if args.text:
            print(args.text)
        if args.ssml:
            print(args.ssml)
    speak(args.text, args.ssml, speaker=SpeakerEnum[args.speaker.upper()], output_file=args.output_file)