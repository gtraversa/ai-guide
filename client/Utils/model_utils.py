from vosk import Model, KaldiRecognizer
import os
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = os.getenv("VOSK")

def load_model(model_path = MODEL_PATH):
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model not found.")
    return Model(model_path)

# def load_recognizer(model = None):
#     if not model:
#         raise Error("")
#     return KaldiRecognizer(model, wf.getframerate())