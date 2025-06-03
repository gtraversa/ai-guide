import lorem
import subprocess
import os
from pathlib import Path


# you can change this to the model you want from https://github.com/coqui-ai/TTS#pretrained-models

def synthesize_text(text: str, tts, output_path: str = Path(__file__).parent/"response.wav"):
    # generate speech and save to output_path
    tts.tts_to_file(text=text, file_path=output_path)

    print(f"Audio saved to {output_path}")
    subprocess.run(["ffplay", "-nodisp", "-autoexit", output_path])
    os.remove(output_path)
    return 

def synthesize_text_openai(client, text: str, output_path: str = Path(__file__).parent/"response.wav"):

    with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="coral",
    input=text,
    instructions="Speak in a cheerful and positive tone.",
) as response: 
        response.stream_to_file(output_path)

    print(f"Audio saved to {output_path}")
    subprocess.run(["ffplay", "-nodisp", "-autoexit", output_path])
    os.remove(output_path)
    return

if __name__ == "__main__":
    sample_text = lorem.sentence()
    synthesize_text(sample_text)