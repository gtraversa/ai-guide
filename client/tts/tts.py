from TTS.api import TTS
import lorem
import subprocess
import os


# you can change this to the model you want from https://github.com/coqui-ai/TTS#pretrained-models

def synthesize_text(text: str, tts, output_path: str = "client/response.wav"):
    # generate speech and save to output_path
    tts.tts_to_file(text=text, file_path=output_path)

    print(f"Audio saved to {output_path}")
    subprocess.run(["ffplay", "-nodisp", "-autoexit", output_path])
    os.remove(output_path)
    return 

if __name__ == "__main__":
    sample_text = lorem.sentence()
    synthesize_text(sample_text)