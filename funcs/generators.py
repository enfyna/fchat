from classes.folder import Folder
from classes.log import Log
from os import remove, path
import torch
import gc


def generate_tts(folders: Folder, voice=None) -> None:
    tts_to_generate = []

    for f in folders:
        sections, section_count = f.get_not_generated_tts()
        if section_count > 0:
            tc_path = f.get_transcriptions_path()
            if tc_path != "":
                remove(tc_path)
                Log.info(f"Removed old transcription: {tc_path}")
        tts_to_generate.extend(sections)

    generate_count = len(tts_to_generate)
    if generate_count == 0:
        Log.info("No need to generate new tts!")
        return

    Log.info(f"Generating {generate_count} tts.")

    from classes.tts import TextToSpeechModel
    tts = TextToSpeechModel()

    i = 1
    count = len(tts_to_generate)
    for section in tts_to_generate:
        Log.info(f"Generating: {len(section[1])} [{i}/{count}]")
        i += 1

        tmp = section[1][0:50]
        Log.info(f"Text: {tmp}...")

        tts.generate(section[1], section[0], voice=voice)

    del tts
    gc.collect()
    torch.cuda.empty_cache()


def generate_transcriptions(folders: Folder) -> None:
    tr_to_generate = []

    count = 0
    for f in folders:
        count += 1
        if f.get_script_path() == "":
            continue
        tc_path = f.get_transcriptions_path()
        if tc_path == "":
            tr_to_generate.append(f)

    generate_count = len(tr_to_generate)
    if generate_count == 0:
        Log.info("No need to generate new transcriptions!")
        return

    from classes.tr import TranscriptionModel
    tr = TranscriptionModel()

    count = 0
    for f in tr_to_generate:
        count += 1
        Log.info(f"Transcribing: {f.name} [{count}/{len(tr_to_generate)}]")
        voiceover_path = f.get_voiceover_path()
        if path.isfile(voiceover_path):
            f.generate_transcriptions(tr)
        else:
            Log.info("No voiceover file found, skipping.")

    del tr
    gc.collect()
    torch.cuda.empty_cache()
