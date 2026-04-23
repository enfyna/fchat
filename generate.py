#!/usr/bin/env python

from os import getenv, path, umask, environ, system, makedirs
from classes.log import Log
from funcs.loaders import load_prefix
from dotenv import load_dotenv
from re import split

load_dotenv()

PREFIX: str = load_prefix()

THREADS = 4
COVER_DURATION = 4

ACCEPT_ALL = (getenv("AA") or getenv("ACCEPT_ALL")) == "1"
PRESET = getenv("PS") or getenv("PRESET")
LOWRES = (getenv("LS") or getenv("LOWRES", "0")) == "1"

FPS = int(getenv("FPS", 24 if not LOWRES else 3))
FINAL_RES_RATIO = float(getenv("FINAL_RES_RATIO", 1.0 if not LOWRES else 0.15))

HEIGHT = int(1280 * FINAL_RES_RATIO)
WIDTH = int(720 * FINAL_RES_RATIO)
Log.info(f"FPS = {FPS}; W/H = {WIDTH}/{HEIGHT}")

CUSTOM_MUSIC_PATH = None
CHAR_PATH = None

STATIC_PATH = getenv("STATIC", path.join(PREFIX, ".static/"))
GLOBAL_MUSIC_PATH = getenv("GLOBAL_MUSIC",
                           path.join(STATIC_PATH, "MusicGlobal"))
if PRESET is None:
    custom_music = getenv("CUSTOM_MUSIC")
    if custom_music is not None:
        CUSTOM_MUSIC_PATH = path.join(STATIC_PATH, custom_music)
    char_path = getenv("CHAR")
    if char_path is not None:
        CHAR_PATH = path.join(STATIC_PATH, char_path)
else:
    CUSTOM_MUSIC_PATH = getenv(
        "CUSTOM_MUSIC", path.join(STATIC_PATH, f"Music{PRESET}"))
    CHAR_PATH = getenv("CHAR", path.join(STATIC_PATH, f"Char{PRESET}"))

if not path.isdir(STATIC_PATH):
    Log.error("Static path does not exist! ")
    Log.error(
        "Try creating a '.static' folder inside your prefix folder."
        "Or check 'STATIC' env variable in '.env' file.")
    if STATIC_PATH is not None and len(STATIC_PATH) > 1:
        input("Do you want to generate an empty static folder to"
              f": {STATIC_PATH} ?")
        for i in \
                (STATIC_PATH, GLOBAL_MUSIC_PATH, CUSTOM_MUSIC_PATH, CHAR_PATH):
            if i is not None:
                makedirs(i, exist_ok=True)
                Log.info(f"Created folder: {i}")
    else:
        exit(1)

IGNORE_LIST = getenv("IGNORE", "") + " .ignore"
IGNORE_LIST = split("[\\s,;]+", IGNORE_LIST.strip())

Log.info(f"STATIC = {STATIC_PATH}")
Log.info(f"IGNORE = {IGNORE_LIST}")
Log.info(f"MUSIC = {GLOBAL_MUSIC_PATH}:{CUSTOM_MUSIC_PATH}")

if True:
    from funcs.loaders import (
        load_font, load_voice, load_global_music, load_char_images
    )

global_musics: list[str] = load_global_music(
    GLOBAL_MUSIC_PATH, CUSTOM_MUSIC_PATH
)
str_music_list = ", ".join([path.basename(m) for m in global_musics])
Log.info(f"MUSICS = {str_music_list}")

CHAR_IMAGE_PATHS: dict = load_char_images(STATIC_PATH, CHAR_PATH)
Log.info(f"CHAR_PATH = [{CHAR_IMAGE_PATHS['count']}]{CHAR_PATH}")

FONT = load_font(STATIC_PATH, getenv("FONT"))
FONT_SIZE = int(getenv("FONT_SIZE", 56) * FINAL_RES_RATIO)
Log.info(f"FONT = [{FONT_SIZE}]{-1 if FONT is None else path.basename(FONT)}")

VOICE = load_voice(STATIC_PATH, getenv("VOICE"))
if VOICE is not None:
    Log.info(f"VOICE = {VOICE}")

umask(0)
environ['FFMPEG_BINARY'] = 'ffmpeg'

if True:
    from classes.folder import Folder

folders, folder_count = Folder.init(
    PREFIX, ignore=IGNORE_LIST, mkmode=0o777)
Folder.info(folders)

for f in folders:
    f.musics.extend(global_musics)

if folder_count == 0:
    Log.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    Log.error("No short folders found!")
    Log.error("Try using 'fauto.py' to generate one.")
    Log.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    exit(0)

if not ACCEPT_ALL:
    input("Continue?")
Log.info("Continuing...")

if True:
    from funcs.generators import generate_transcriptions, generate_tts
Log.info("Generators loaded...")

if True:
    from classes.short import ShortBuilder
Log.info("Moviepy loaded...")


def main() -> None:
    ShortBuilder.init(
        HEIGHT, WIDTH,
        FONT, FONT_SIZE,
        COVER_DURATION,
        CHAR_IMAGE_PATHS,
        FPS, THREADS, LOWRES
    )

    generate_tts(folders, VOICE)

    if FONT is not None:
        generate_transcriptions(folders)

    count = 0
    for f in folders:
        count += 1
        try:
            Log.info(f"Generating short: {f.name} [{count}/{folder_count}]")
            lowres_prefix = "lowres-" if LOWRES else ""
            short_name = f"{lowres_prefix}{f.name}.mp4"
            short_path = path.join(PREFIX, short_name)
            if not path.isfile(short_path):
                ShortBuilder(f, short_path)
            else:
                Log.info("Short already generated.")
        except Exception as e:
            Log.error(f"Error generating short for {f.name}: {e}")
            continue

    Log.info("Shorts are ready.")

    for _ in range(50):
        system("notify-send -a fchat -i gtk-save -t 3000 "
               "'Rendering Completed' 'Check the results'")


if __name__ == "__main__":
    main()
    Log.end()
