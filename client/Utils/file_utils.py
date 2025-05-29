import os
from dotenv import load_dotenv
import shutil

load_dotenv()

REC_DIRECTORY = os.getenv("REC_DIRECTORY")

def clear_recordings():
    if os.path.exists(REC_DIRECTORY):
        shutil.rmtree(REC_DIRECTORY)
        print("Recordings cleared.")

def make_rec_dir():
    os.makedirs(REC_DIRECTORY, exist_ok=True)
    return REC_DIRECTORY