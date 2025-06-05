import logging
import re
from dotenv import load_dotenv
from typing import AsyncIterable, Optional, List, Dict
import asyncio

from livekit import rtc,api,agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, get_job_context,cli, WorkerOptions
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)
from livekit.agents.voice.agent_activity import StopResponse
from livekit.agents.llm import ChatContext
from livekit.plugins.turn_detector.english import EnglishModel

load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

WAKE_WORD = "hey enzo"

class AI_Guide(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a statue of Enzo Ferrari in a museum. Guests will be asking you questions regarding yourself," \
                                        " your life, the history of Ferrari. Guests will also be asking you general questions unrelated to yourself." \
                                        "Keep the responses brief and concise, but add a little flare to make them less serious.")
        self.wake_word_detected = False
        self.wake_word = WAKE_WORD

    async def on_enter(self):
        # Inform the user that the agent is waiting for the wake word
        logger.info(f"Waiting for wake word: '{WAKE_WORD}'")
        # We don't want to generate a reply immediately anymore
        self.session.say(f"Waiting for wake word: '{WAKE_WORD}'")

    def stt_node(self, audio: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(audio, model_settings)

        if parent_stream is None:
            return None

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text.lower()
                    logger.info(f"Received transcript: '{transcript}'")

                    # Clean the transcript by removing punctuation and extra spaces
                    cleaned_transcript = re.sub(r'[^\w\s]', '', transcript)  # Remove punctuation
                    cleaned_transcript = ' '.join(cleaned_transcript.split())  # Normalize spaces
                    logger.info(f"Cleaned transcript: '{cleaned_transcript}'")

                    if not self.wake_word_detected:
                        # Check for wake word in cleaned transcript
                        if self.wake_word in cleaned_transcript:
                            logger.info(f"Wake word detected: '{self.wake_word}'")
                            self.wake_word_detected = True

                            # Extract content after the wake word
                            content_after_wake_word = cleaned_transcript.split(self.wake_word, 1)[-1].strip()
                            if content_after_wake_word:
                                # Replace the transcript with only the content after the wake word
                                event.alternatives[0].text = content_after_wake_word
                                yield event
                        # If wake word not detected, don't yield the event (discard input)
                    else:  
                        # Wake word already detected, process this utterance
                        yield event
                elif self.wake_word_detected:
                    # Pass through other event types (like START_OF_SPEECH) when wake word is active
                    yield event

        return process_stream()
    
    async def on_user_turn_completed(self, chat_ctx, new_message=None):  
        # Only generate a reply if the wake word was detected  
        if self.wake_word_detected:  
            # Let the default behavior happen  
            result = await super().on_user_turn_completed(chat_ctx, new_message)
            return result
        # Otherwise, don't generate a reply
        raise StopResponse()
    
    async def user_timeout(self):
        if self.wake_word_detected:
            self.wake_word_detected = False
        logger.info("User timed out, chat reset")
        await self.update_chat_ctx(ChatContext())

    @function_tool()
    async def end_conversation(self) -> None:
        """
        End the conversation when the user signals so.
        """
        await self.session.generate_reply(
            instructions="Tell the user a friendly goodbye, like Enzo Ferrari would. Keep it short"
        )
        self.wake_word_detected = False
        logger.info("Response completed, waiting for wake word again")
        await self.update_chat_ctx(ChatContext())

async def entrypoint(ctx: agents.JobContext):
    agent = AI_Guide()
    session = AgentSession(
        stt=openai.STT(model = 'whisper-1'),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=openai.TTS(
            model = 'tts-1',
            voice="ash",
            instructions="Speak in a friendly and conversational tone.",
            ),
        vad=silero.VAD.load(),
        turn_detection=EnglishModel(),
        user_away_timeout=15,
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    @session.on("user_state_changed")
    def on_user_state_changed(event):
        asyncio.create_task(agent.user_timeout())


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))