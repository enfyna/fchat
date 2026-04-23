from pydub import AudioSegment
from pathlib import Path
from PIL import Image
from classes.log import Log
import tiktoken
import semchunk
import json
import os


class Folder:
    path: str
    path_build: str
    path_tts: str
    videos: list[str]
    images: list[str]
    texts: list[str]  # text files
    tts: list[str]  # generated tts files

    captions: list[str]  # texts to generate tts

    isValid: bool
    err: str = "OK"

    def __init__(self, path: str, voice: str = "", mkmode=0o777):
        self.path = os.path.dirname(path)
        self.path_build = os.path.join(self.path, "build")
        self.path_tts = os.path.join(self.path_build, "tts")

        self.name = os.path.basename(self.path)

        self.isValid = True

        if not os.path.exists(self.path):
            self.err = f"[ERROR] Doesnt exist! {self.path} "
            print(self.err)
            self.isValid = False
            return

        if not os.path.isdir(self.path):
            self.err = f"[ERROR] Not a folder! {self.path} "
            print(self.err)
            self.isValid = False
            return

        Folder.convert_images_to_png(self.path)

        self.videos, video_count = self.find_files("mp4", "gif")
        self.musics, music_count = self.find_files("mp3")
        self.images, image_count = self.find_files("jpg", "jpeg", "png")
        self.texts, text_count = self.find_files("txt")

        if image_count == 0 and video_count == 0:
            self.err = f"[ERROR] No images or videos found! {self.path}"
            print(self.err)
            self.isValid = False
            return

        if (out := self.get_chat_output_path()) != "":
            self.convert_chat_output_to_files(out)

        sp = self.get_script_path()
        if sp == "":
            # self.err = f"[ERROR] No script found! {self.path}"
            # self.isValid = False
            self.captions = []
            self.tts = []
            return

        with open(sp, "r") as f:
            text = f.read()
            chunker = Folder.get_chunker(100)
            self.captions = chunker(text)

        self.tts = []

        for i in range(len(self.captions)):
            voice_name = f"_{voice}" if len(voice) > 0 else ""
            outfile = f"{self.path_tts}/{i}{voice_name}.wav"
            self.tts.append(outfile)

        if not os.path.exists(self.path_tts):
            os.makedirs(self.path_tts, mode=mkmode, exist_ok=True)

        return

    def get_not_generated_tts(self) -> (list[str], int):
        not_generated = []
        for i in range(len(self.captions)):
            if not os.path.isfile(self.tts[i]):
                not_generated.append((self.tts[i], self.captions[i]))
        return not_generated, len(not_generated)

    def get_voiceover_path(self) -> str:
        voiceover_path = f"{self.path_tts}/voice.wav"
        if not os.path.isfile(voiceover_path):
            combined = AudioSegment.empty()
            for tts in self.tts:
                combined += AudioSegment.from_wav(tts)
            combined.export(voiceover_path, format="wav")
        return voiceover_path

    def get_cover_image_path(self) -> str:
        for im in self.images:
            if os.path.basename(im).split(".")[0] == "cover":
                return im
        return ""

    def get_brainrot_path(self) -> str:
        for tx in self.videos:
            if os.path.basename(tx).split(".")[0] == "brainrot":
                return tx
        return ""

    def get_chat_output_path(self) -> str:
        for tx in self.texts:
            if os.path.basename(tx).split(".")[0] == "chat":
                return tx
        return ""

    def get_script_path(self) -> str:
        for tx in self.texts:
            if os.path.basename(tx).split(".")[0] == "script":
                return tx
        return ""

    def get_comment_path(self) -> str:
        for tx in self.texts:
            if os.path.basename(tx).split(".")[0] == "comment":
                return tx
        return ""

    def get_youtube_req(self) -> (dict, str):
        for tx in self.texts:
            if os.path.basename(tx).split(".")[0] == "youtube":
                try:
                    j = json.load(open(tx, "r"))
                    return j, tx
                except Exception as ex:
                    Log.warn(f"Invalid youtube json: {tx}")
                    Log.warn(f"Reason: {ex}")
        return None, None

    def find_files(self, *exts, path=None) -> (list, int):
        if path is None:
            path = self.path
        files = []
        if not os.path.isdir(path):
            Log.error(f"Not a valid path: {path}")
            return ([], -1)
        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            if not os.path.isfile(full_path):
                continue
            if f.split(".")[-1] in exts:
                files.append(full_path)
        return files, len(files)

    def get_transcriptions_path(self) -> str:
        if os.path.isdir(self.path_build):
            txts, count = self.find_files("txt", path=self.path_build)
            for f in txts:
                if os.path.basename(f).split(".")[0] == "transcriptions":
                    return f
        return ""

    def generate_transcriptions(self, tr_model) -> None:
        Log.info(f"Generating transcriptions for {self.name}...")
        self.word_stamps, self.segment_stamps = tr_model.transcribe(
            self.get_voiceover_path()
        )

        transcription_file = f"{self.path_build}/transcriptions.txt"
        with open(transcription_file, "w") as f:
            json.dump({
                "words": self.word_stamps,
                "segments": self.segment_stamps
            }, f, indent=None)
        Log.info(f"Transcriptions saved to {transcription_file}")
        return

    def get_transcriptions(self) -> (dict, dict):
        trnscrpt_path = self.get_transcriptions_path()
        if trnscrpt_path == "":
            return None, None
        with open(trnscrpt_path, "r") as f:
            j: dict = json.load(f)
            self.word_stamps = j.get("words")
            self.segment_stamps = j.get("segments")
        return self.word_stamps, self.segment_stamps

    def convert_chat_output_to_files(self, path: str) -> None:
        Log.info(f"Converting chat output: {path}")
        lines: list[str] = []
        with open(path, "r") as f:
            lines = f.readlines()

        clean_lines: list[str] = [i.strip() for i in lines]
        files: dict = {}

        last_file = ""
        for line in clean_lines:
            if line.endswith(".txt"):
                files[line] = []
                last_file = line
            else:
                if last_file == "":
                    Log.error("Couldnt convert chat.txt to files!")
                    return 1
                files[last_file].append(line)

        for file in files.keys():
            text = "".join(files[file])
            file_path = os.path.join(self.path, file)
            with open(file_path, "w") as f:
                written = f.write(text)
                Log.info(f"Written({written}): {file_path}")

            self.texts.append(file_path)

        os.remove(path)

        return

    @staticmethod
    def init(path: str, voice: str = "",
             ignore: list[str] = [], mkmode=0o777) -> (list, int):
        folders = []
        for name in os.listdir(path):
            if name in ignore:
                continue
            if name.startswith("."):
                continue
            folder = os.path.join(path, name) + "/"
            if not os.path.isdir(folder):
                continue
            f = Folder(folder, voice, mkmode)
            if f.isValid:
                folders.append(f)
        return folders, len(folders)

    encoding: tiktoken.Encoding = None

    @staticmethod
    def get_encoding():
        if Folder.encoding is None:
            Log.info("Loading encoding...")
            Folder.encoding = tiktoken.encoding_for_model("gpt-4")
        return Folder.encoding

    @staticmethod
    def get_chunker(chunk_size: int):
        os.environ["TIKTOKEN_CACHE_DIR"] = "./tiktoken_cache/"
        return semchunk.chunkerify(Folder.get_encoding(), chunk_size)

    @staticmethod
    def convert_images_to_png(folder):
        folder = Path(folder)
        for file in folder.iterdir():
            suffix = file.suffix.lower()
            if suffix in [".webp", ".avif"]:
                try:
                    img = Image.open(file).convert("RGBA")
                    new_file = file.with_suffix(".png")
                    img.save(new_file, "PNG")
                    os.remove(file)
                    Log.info(f"Converted {suffix}: {new_file.name}")
                except Exception as e:
                    Log.error(f"Failed to convert {file.name}: {e}")

    @staticmethod
    def info(fs: list):
        tts_not_generated = 0
        Log.info("Listing folders...")
        print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for f in fs:
            name = f"{f.name[0:48]}..." if len(f.name) > 52 else f.name
            print(f"┣┳━► {name}")

            ic = len(f.images)
            vc = len(f.videos)
            mc = len(f.musics)
            tc = len(f.texts)
            cc = len(f.captions)

            _, tts = f.get_not_generated_tts()
            tts_not_generated += tts

            mat_counts = (f"{ic} images, {vc} videos, {mc} musics, "
                          f"{tc} texts, ({cc-tts}/{cc}) caps")

            has_cover_image = \
                ", Cover Image" if f.get_cover_image_path() else ""
            has_script = ", Script" if f.get_script_path() else ""
            has_brainrot = ", Brainrot" if f.get_brainrot_path() else ""
            has_tc = ", Transcript" if f.get_transcriptions_path() else ""
            has_bgm = ", BGM" if len(f.musics) > 0 else ""
            has_youtube = ", Youtube" if f.get_youtube_req()[0] else ""
            has_comment = ", Comment" if f.get_comment_path() else ""
            spec_list = [
                has_cover_image, has_script, has_brainrot, has_tc, has_bgm,
                has_youtube, has_comment
            ]
            specs = "".join([s for s in spec_list if s != ""])

            print(f"┃┗━━━► {mat_counts}{specs}.")

        str_gen = f"TTS to generate: {tts_not_generated}"
        str_srt = f"Short count: {len(fs)}"

        print("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
        print(f"┃{str_srt.center(30)}┃")
        print(f"┃{str_gen.center(30)}┃")
        print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
        return


if __name__ == "__main__":
    fs, f_count = Folder.init("/mnt/Shares/Public/")
    Folder.info(fs)
