from vosk import KaldiRecognizer
import os
import wave
import json


def get_latest_audio_file(base_dir):
    files = [os.path.join(base_dir, f) for f in os.listdir(base_dir)
             if os.path.isfile(os.path.join(base_dir, f)) and f.endswith(".wav")]
    if not files:
        print("No recordings found.")
        return None
    return max(files, key=os.path.getmtime)

def transcribe_audio(file_path, model):

    wf = wave.open(file_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
        print("Audio file must be WAV mono PCM 16-bit 16kHz.")
        return None

    rec = KaldiRecognizer(model, wf.getframerate())

    text_result = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            print(result)
            text_result += result.get("text", "") + " "

    # Get final bits
    final_result = json.loads(rec.FinalResult())
    text_result += final_result.get("text", "")

    wf.close()
    return text_result.strip()


if __name__ == "__main__":
    audio_file = get_latest_audio_file()
    if audio_file:
        result = transcribe_audio(audio_file)
        print(result)
    else:
        print("No audio file found.")