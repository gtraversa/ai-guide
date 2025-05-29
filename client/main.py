import os
from audio_io.mic_listener import record_audio
from stt.stt import transcribe_audio, get_latest_audio_file
from dotenv import load_dotenv
from Utils.file_utils import clear_recordings,make_rec_dir
from Utils.model_utils import load_model

load_dotenv()

REC_DIRECTORY = make_rec_dir()
MODEL = load_model()

def main():
    try:
        user_input = input("Press Enter to record or type 'q' to quit: ").strip().lower()
        while True:
            if user_input == 'q':
                break
            record_audio(REC_DIRECTORY)
            audio_file = get_latest_audio_file(REC_DIRECTORY)
            if audio_file:
                text = transcribe_audio(audio_file, MODEL)
                print(f"Transcription: {text}")
            else:
                print("No audio recorded.")

            cont = input("Record again? (y/n): ").strip().lower()
            if cont != 'y':
                break
    except KeyboardInterrupt:
        print("\nExiting...")

    clear_recordings()

if __name__ == "__main__":
    main()