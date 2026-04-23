import os
import wave
import torch
import numpy as np
from classes.log import Log


class TextToSpeechModel:
    def __init__(self):
        Log.info("Loading TTS model: ChatterboxTTS")
        from chatterbox.tts import ChatterboxTTS
        self.model = ChatterboxTTS.from_pretrained(device="cuda")
        return

    def generate(self, txt: str, outfile: str, voice: str) -> None:
        with wave.open(outfile, "wb") as wf:
            wf.setnchannels(1)  # mono
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(self.model.sr)

            out = self.model.generate(txt, audio_prompt_path=voice)

            for chunk in out:
                if isinstance(chunk, torch.Tensor):
                    chunk = chunk.detach().cpu().numpy()

                chunk = np.asarray(chunk).squeeze()

                # convert float32 [-1,1] → int16
                pcm16 = np.clip(chunk, -1, 1)
                pcm16 = (pcm16 * 32767).astype(np.int16)

                wf.writeframes(pcm16.tobytes())
        os.chmod(outfile, 0o777)
