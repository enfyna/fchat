from os import getenv, path, listdir
from classes.log import Log


def load_global_music(global_path, custom_path) -> list[str]:
    global_musics: list[str] = []
    if global_path is not None and path.exists(global_path):
        for f in listdir(global_path):
            if path.basename(f).endswith(".mp3"):
                global_musics.append(path.join(global_path, f))
    if custom_path is not None and path.exists(custom_path):
        for f in listdir(custom_path):
            if path.basename(f).endswith(".mp3"):
                global_musics.append(path.join(custom_path, f))
    return global_musics


def load_char_images(static_path, char_path) -> dict:
    char_image_paths: dict = {
        'silent': "",
        'talk': [],
        'count': 0,
    }

    if static_path is None or char_path is None:
        return char_image_paths

    char_path = path.join(static_path, char_path)
    if not path.exists(char_path):
        return char_image_paths

    silent_found = False
    for f in listdir(char_path):
        if path.basename(f).endswith(".png"):
            if path.basename(f).find("silent") >= 0:
                char_image_paths['silent'] = path.join(char_path, f)
                silent_found = True
            else:
                char_image_paths['talk'].append(path.join(char_path, f))
            char_image_paths['count'] += 1

    if not silent_found:
        char_image_paths['count'] = 0

    return char_image_paths


def load_font(static_path, font) -> str:
    if font is not None and not path.isfile(font):
        raise ValueError(f"[ERROR] Couldnt open font {font}")

    found = False
    if font is None and path.exists(static_path):
        for f in listdir(static_path):
            if path.basename(f).endswith(".ttf"):
                font = path.join(static_path, f)
                found = True
                break
    if found is False:
        Log.warn(f"Couldnt find font file: {font}")
        Log.warn("Place a font file '.ttf' inside your static folder.")
        Log.warn("Or provide the path using the 'FONT' env variable.")

    return font


def load_voice(static_path, voice) -> str:
    if voice is None and path.exists(static_path):
        for f in listdir(static_path):
            if path.basename(f).endswith(".wav"):
                voice = f
                break
    if voice is not None:
        if not path.isfile(voice):
            raise ValueError(f"[ERROR] Couldnt open voice {voice}")
    return voice


def load_prefix() -> str:
    prefix = getenv("PREFIX")
    if prefix is None:
        Log.error(f"PREFIX is None! ({prefix})")
        Log.info("Add a PREFIX key to the '.env' file.")
        Log.info("PREFIX is where the shorts are going to be generated.")
        exit(1)
    elif path.isdir(prefix) is False:
        Log.error(f"PREFIX is not a valid directory! ({prefix})")
        Log.info("Fix the PREFIX key in the '.env' file.")
        Log.info("PREFIX is where the shorts are going to be generated.")
        exit(1)
    else:
        Log.info(f"PREFIX = {prefix}")
    return prefix
