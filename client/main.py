import os
from audio_io.mic_listener import record_audio
from stt.stt import transcribe_audio, get_latest_audio_file, whisper_transcribe
from tts.tts import synthesize_text,synthesize_text_openai
from dotenv import load_dotenv
from Utils.file_utils import clear_recordings,make_rec_dir
from Utils.model_utils import load_stt_model,load_tts_model, load_openai_client
from llm.llm_interact import send_llm


load_dotenv()

REC_DIRECTORY = make_rec_dir()
STT_MODEL = load_stt_model()
TTS_MODEL = load_tts_model()
client = load_openai_client()
prev_q_id = None

def main():
    try:
        prev_q_id = None
        user_input = input("Press Enter to record or type 'q' to quit: ").strip().lower()
        while True:
            if user_input == 'q':
                break
            record_audio(REC_DIRECTORY)
            audio_file = get_latest_audio_file(REC_DIRECTORY)
            if audio_file:
                #text = transcribe_audio(audio_file, STT_MODEL)
                text = whisper_transcribe(audio_file, client)
                print(f"Transcription: {text}")
                (response,prev_q_id) = send_llm(text, prev_q_id,client)
                print(f'Response: {response}')
                synthesize_text_openai(client,response)

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