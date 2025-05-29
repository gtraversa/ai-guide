from vosk import Model, KaldiRecognizer
import os
from dotenv import load_dotenv
from TTS.api import TTS

load_dotenv()

TTS_MODEL_PATH = os.getenv("VOSK")
SST_MODEL = os.getenv("TTS")

def load_stt_model(model_path = TTS_MODEL_PATH):
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model not found.")
    return Model(model_path)

def load_tts_model():
    return TTS(SST_MODEL)


# def load_recognizer(model = None):
#     if not model:
#         raise Error("")
#     return KaldiRecognizer(model, wf.getframerate())