from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from classes.log import Log
import torch


class TranscriptionModel():
    def __init__(self):
        model_id = "openai/whisper-large-v3-turbo"

        Log.info("Loading transcription model: " + model_id)

        isCudaAvailable = torch.cuda.is_available()

        self.device = "cuda:0" if isCudaAvailable else "cpu"
        torch_dtype = torch.float16 if isCudaAvailable else torch.float32

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            # low_cpu_mem_usage=True,
            use_safetensors=True,
        )
        self.model.to(self.device)

        self.processor = AutoProcessor.from_pretrained(model_id)

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=self.device,
        )

        return

    def transcribe(self, file: str):
        word_timestamps = self.pipe(
            file,
            return_timestamps="word",
            generate_kwargs={"language": "english"}
        )
        segment_timestamps = self.pipe(
            file,
            return_timestamps=True,
            generate_kwargs={"language": "english"}
        )
        # print("-------------------------------------------------")
        # print(word_timestamps['text'], segment_timestamps['text'])
        assert (word_timestamps['text'] == segment_timestamps['text'])
        return word_timestamps['chunks'], segment_timestamps['chunks']
