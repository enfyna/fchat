from moviepy import (
    CompositeVideoClip,
    CompositeAudioClip,
    AudioFileClip,
    VideoFileClip,
    ImageClip,
    TextClip,
    audio,
    vfx,
)
from classes.folder import Folder
from classes.log import Log
import random
import os
import re


class ShortBuilder:

    THREADS = 4
    LOWRES = False
    FPS = 60
    WIDTH = 1080
    HEIGHT = 1920
    COVER_DURATION = 5
    FONT = "Arial-Bold"
    FONT_SIZE = 96
    VTUBE = {
        'count': 0,
        'silent': "",
        'talk': []
    }

    def __init__(self, folder: Folder, name: str):
        self.folder: Folder = folder
        self.duration: float = 0
        self.backgrounds: list = []
        self.bg_duration: float = 0
        self.captions: list = []
        self.ct_duration: float = 0
        self.bgms: list = []
        self.bgm_duration: float = 0

        audio_list = []
        voice = None

        if self.folder.get_brainrot_path() != "":
            voice = AudioFileClip(self.folder.get_voiceover_path())
            brainrot = ShortBuilder.load_video_clip(
                self.folder.get_brainrot_path(), voice.duration, True
            )
            self.backgrounds.append(brainrot)
            audio_list.append(brainrot.audio.with_start(voice.duration))
            self.duration = brainrot.duration + voice.duration
            self = self.fill_vtube(voice.duration)
        else:
            if self.folder.get_script_path() != "":
                voice = AudioFileClip(self.folder.get_voiceover_path())\
                    .with_effects([audio.fx.AudioNormalize()])
                self.duration = voice.duration
            else:
                self.duration = 20

            self = self.add_cover().remove_cover_image_from_list()\
                .shuffle_resources().use_all_videos_until()\
                .shuffle_resources().fill_bg()\
                .fill_vtube()\
                .fill_music(0.2 if voice is not None else 0.7)

        if voice is not None:
            audio_list.append(voice)
            self.fill_subtitles()
        else:
            self.duration = self.bg_duration

        audio_list.extend(self.bgms)

        Log.info("Starting compositing.")

        composite_audio = None
        if len(audio_list) > 0:
            composite_audio = CompositeAudioClip(audio_list)\
                .with_duration(self.duration)

        video = CompositeVideoClip(
            [*self.backgrounds, *self.captions],
            size=(ShortBuilder.WIDTH, ShortBuilder.HEIGHT),
            bg_color=(0, 0, 0),
        )\
            .with_duration(self.duration)\
            .with_audio(composite_audio)

        Log.info("Starting write_videofile.")

        use_nvidia = "_nvenc" if not ShortBuilder.LOWRES else ""
        video.write_videofile(
            name,
            codec=f"h264{use_nvidia}",
            audio_codec="aac",
            fps=ShortBuilder.FPS,
            threads=ShortBuilder.THREADS,
            preset="fast",
        )

        for au in audio_list:
            au.close()
        for v in self.backgrounds:
            if isinstance(v, VideoFileClip):
                v.close()

        self.backgrounds.clear()
        self.captions.clear()
        return

    @staticmethod
    def init(height: int, width: int,
             font, font_size,
             cover_duration, vtube_image_paths,
             fps: int, threads: int, lowres: bool):
        ShortBuilder.HEIGHT = height
        ShortBuilder.WIDTH = width
        ShortBuilder.FPS = fps
        ShortBuilder.THREADS = threads
        ShortBuilder.COVER_DURATION = cover_duration
        ShortBuilder.FONT = font
        ShortBuilder.FONT_SIZE = font_size
        ShortBuilder.LOWRES = lowres
        char_silent = vtube_image_paths['silent']
        vtube_images = {
            'silent': "" if char_silent == "" else
            ImageClip(char_silent).resized(width=ShortBuilder.WIDTH / 3.0),
            'talk': [ImageClip(i) .resized(width=ShortBuilder.WIDTH / 3.0)
                     for i in vtube_image_paths['talk']],
            'count': vtube_image_paths['count'],
        }
        ShortBuilder.VTUBE = vtube_images
        return

    @staticmethod
    def zoom_image_size(size, time=10, scale_factor=0.3):
        def zoom_image(t):
            scale = scale_factor * size
            if t < time:
                return size + (-(1-t/time)**2 * 0.5 + 1) * scale
            else:
                return size + scale
        return zoom_image

    @staticmethod
    def load_video_clip(path: str, start: float, audio=False) -> VideoFileClip:
        return VideoFileClip(
            path, audio, target_resolution=(None, ShortBuilder.HEIGHT))\
            .with_position(("center", "center"))\
            .with_start(start)\
            .with_effects([
                vfx.FadeIn(0.2),
                vfx.FadeOut(0.2),
            ])

    @staticmethod
    def load_image_clip(
            path: str, start: float, duration: float,
            fadeIn: float = 0.2, fadeOut: float = 0.2) -> tuple[ImageClip]:
        im = ImageClip(path)\
            .with_position(('center', 'center'))\
            .with_duration(duration)\
            .with_start(start)\
            .with_effects([vfx.FadeIn(fadeIn), vfx.FadeOut(fadeOut)])
        return (
            im.with_effects([
                vfx.Resize(height=ShortBuilder.zoom_image_size(
                    ShortBuilder.HEIGHT * 1.2,
                    time=0,
                    scale_factor=-0.2)),
                vfx.HeadBlur(fx=lambda t: 0,
                             fy=lambda t: 0,
                             radius=9999999,
                             intensity=2),
                vfx.MultiplyColor(0.2),
            ]),
            im.with_effects([
                vfx.Resize(width=ShortBuilder.zoom_image_size(
                    ShortBuilder.WIDTH)),
            ]),
        )

    def use_all_videos_until(self) -> "ShortBuilder":
        for i in range(len(self.folder.videos)):
            video = ShortBuilder.load_video_clip(
                self.folder.videos[i], self.bg_duration)
            video_duration = 0
            video_file_name = os.path.basename(
                self.folder.videos[i]).split(".")[0]
            split_name = "sec"
            for p in video_file_name.split("_"):
                if p.lower().find(split_name) > 0:
                    Log.info(f"Video duration found for:\
     {video_file_name} at: {p.lower()}")
                    video_duration = int(p.lower().split(split_name)[0])
                    video.with_duration(video_duration)
                    self.bg_duration += video_duration
                    break
            else:
                self.bg_duration += video.duration
            self.backgrounds.append(video)
            if self.bg_duration > self.duration:
                break
        return self

    def add_cover(self) -> "ShortBuilder":
        cover_image_path = self.folder.get_cover_image_path()
        if cover_image_path != "":
            Log.info(f"Cover image found: {cover_image_path}")
            self.backgrounds.extend(
                ShortBuilder.load_image_clip(
                    cover_image_path,
                    self.bg_duration,
                    ShortBuilder.COVER_DURATION,
                    fadeIn=0,
                )
            )
            self.bg_duration += ShortBuilder.COVER_DURATION
        return self

    def remove_cover_image_from_list(self) -> "ShortBuilder":
        if len(self.folder.images) > 0 \
                and self.folder.get_cover_image_path() in self.folder.images:
            self.folder.images.remove(self.folder.get_cover_image_path())
        return self

    def shuffle_resources(self) -> "ShortBuilder":
        random.shuffle(self.folder.images)
        random.shuffle(self.folder.videos)
        random.shuffle(self.folder.musics)
        return self

    def fill_subtitles(self) -> "ShortBuilder":
        if ShortBuilder.FONT is None:
            return

        word_stamps, segment_stamps = self.folder.get_transcriptions()

        margin = (ShortBuilder.FONT_SIZE // 2, ShortBuilder.FONT_SIZE // 2)

        if False:
            for word in word_stamps:
                words = word['text'].strip()

                word_duration = word['timestamp'][1] - word['timestamp'][0]
                text_clip: TextClip = TextClip(
                    ShortBuilder.FONT,
                    text=words,
                    method='label',
                    # size=(WIDTH - 220, 48),
                    margin=margin,
                    text_align="center",
                    color="white",
                    font_size=ShortBuilder.FONT_SIZE,
                    stroke_color="black",
                    stroke_width=16,
                    bg_color="black",
                    duration=word_duration
                )\
                    .with_start(word['timestamp'][0])\
                    .with_position(('center', 'center'))

                self.captions.append(text_clip)

        else:
            chunker = Folder.get_chunker(4)

            used_words = 0
            for sent_st in segment_stamps:
                sents = chunker(sent_st['text'].strip())

                for words in sents:
                    words = words.strip()
                    word_list = re.split("[\\s]+", words)
                    current_text: str = ""
                    last_end: float = 0
                    for _ in word_list:
                        if used_words >= len(word_stamps):
                            break
                        word = word_stamps[used_words]
                        start = word['timestamp'][0]
                        end = word['timestamp'][1]
                        used_words += 1

                        word_duration = end - start
                        if abs(last_end - start) > 0.01:
                            current_text = ""
                        last_end = end

                        if len(current_text) > 16:
                            current_text = ""

                        current_text += word['text']
                        current_text = current_text.strip()

                        highlight: bool = current_text.find("%") != -1 \
                            or len(word_list) == 1
                        text_clip: TextClip = TextClip(
                            ShortBuilder.FONT,
                            text=current_text,
                            method='label',
                            # size=(WIDTH - 220, 48),
                            margin=margin,
                            text_align="center",
                            color="lime" if highlight else "white",
                            font_size=ShortBuilder.FONT_SIZE,
                            # stroke_color="black",
                            # stroke_width=16,
                            bg_color="black",
                            duration=word_duration
                        )\
                            .with_position(('center', 0.7), relative=True)\
                            .with_start(start)

                        self.captions.append(text_clip)

                        if current_text.endswith(". "):
                            current_text = ""
        ###
        while used_words < len(word_stamps):
            word = word_stamps[used_words]
            start = word['timestamp'][0]
            end = word['timestamp'][1]
            used_words += 1

            word_duration = end - start
            if abs(last_end - start) > 0.01:
                current_text = ""
            last_end = end

            if len(current_text) > 16:
                current_text = ""

            current_text += word['text']
            current_text = current_text.strip()
            text_clip: TextClip = TextClip(
                ShortBuilder.FONT,
                text=current_text,
                method='label',
                # size=(WIDTH - 220, 48),
                margin=margin,
                text_align="center",
                color="white",  # if len(current_text.split(" ")) > 1
                # else "lime",
                font_size=ShortBuilder.FONT_SIZE,
                # stroke_color="black",
                # stroke_width=16,
                bg_color="black",
                duration=word_duration
            )\
                .with_start(start)\
                .with_position(('center', 0.7), relative=True)

            self.captions.append(text_clip)

            if current_text.endswith(". "):
                current_text = ""

        return self

    def fill_bg(self) -> "ShortBuilder":
        while self.bg_duration < self.duration:
            if len(self.folder.images) > 0:
                image_duration = max(
                    2, (self.duration - self.bg_duration) /
                    len(self.folder.images)
                )
                for im in self.folder.images:
                    self.backgrounds.extend(
                        ShortBuilder.load_image_clip(
                            im, self.bg_duration, image_duration,
                            0 if len(self.backgrounds) == 0 else 0.2)
                    )
                    self.bg_duration += image_duration
                    if self.bg_duration >= self.duration:
                        break
            elif len(self.folder.videos) > 0:
                for vid in self.folder.videos:
                    video = ShortBuilder.load_video_clip(
                        vid, self.bg_duration)
                    self.backgrounds.append(video)
                    self.bg_duration += video.duration
                    if self.bg_duration >= self.duration:
                        break
            else:
                Log.error("No bg found! Generated short will have black bg!")
                break
        return self

    def fill_music(self, volume: float) -> "ShortBuilder":
        if len(self.folder.musics) > 0:
            while self.bgm_duration < self.duration:
                for m in self.folder.musics:
                    au = AudioFileClip(m)\
                        .with_start(self.bgm_duration)\
                        .with_effects([
                            audio.fx.AudioNormalize(),
                        ])\
                        .with_effects([
                            audio.fx.MultiplyVolume(volume),
                        ])
                    usable_duration = self.duration - self.bgm_duration
                    if usable_duration < au.duration:
                        au = au.with_duration(usable_duration)
                    self.bgm_duration += au.duration
                    self.bgms.append(au)
                    if self.bgm_duration >= self.duration:
                        break

            self.bgms[-1] = self.bgms[-1]\
                .with_effects([audio.fx.AudioFadeOut(duration=4)])

            self.bgms[0] = self.bgms[0]\
                .with_effects([audio.fx.AudioFadeIn(duration=2)])

        return self

    def fill_vtube(self, max_duration=None) -> "ShortBuilder":
        if ShortBuilder.VTUBE['count'] == 0:
            return self
        if ShortBuilder.VTUBE['silent'] == "":
            return self
        if len(ShortBuilder.VTUBE['talk']) == 0:
            return self

        word_stamps, segment_stamps = self.folder.get_transcriptions()
        if word_stamps is None or len(word_stamps) == 0:
            return self

        pos = ("left", 0.55)

        last_end = 0

        for word in word_stamps:
            start = word['timestamp'][0]
            end = word['timestamp'][1]

            if start > last_end:
                self.backgrounds.append(
                    ShortBuilder.VTUBE['silent']
                    .with_position(pos, relative=True)
                    .with_duration(start - last_end)
                    .with_start(last_end)
                )

            last_end = end

            word_duration = end - start
            img_duration = word_duration / 2

            rotation = random.uniform(-15.0, 15.0)
            self.backgrounds.extend((
                random.choice(ShortBuilder.VTUBE['talk'])
                .with_position(pos, relative=True)
                .with_duration(img_duration)
                .with_start(start)
                .with_effects([
                    vfx.Rotate(rotation, expand=False),
                ]),
                random.choice(ShortBuilder.VTUBE['talk'])
                .with_position(pos, relative=True)
                .with_duration(img_duration)
                .with_start(start + img_duration)
                .with_effects([
                    vfx.Rotate(rotation, expand=False),
                ])
            ))

        end_time = self.duration if max_duration is None else max_duration

        self.backgrounds.append(
            ShortBuilder.VTUBE['silent']
            .with_position(pos, relative=True)
            .with_duration(end_time - last_end)
            .with_start(last_end)
        )

        return self
