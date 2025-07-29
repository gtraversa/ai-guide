import logging
from dotenv import load_dotenv
from typing import AsyncIterable, Optional
import asyncio

from livekit import rtc,agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool,cli, WorkerOptions
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)
from livekit.agents.voice.agent_activity import StopResponse
from livekit.agents.llm import ChatContext
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import RPi.GPIO as GPIO 

from led import Pixels

led = Pixels()

BUTTON = 17


load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)


class AI_Guide(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a statue of Enzo Ferrari in a museum. Guests will be asking you questions regarding yourself," \
                                        " your life, the history of Ferrari. Guests will also be asking you general questions unrelated to yourself." \
                                        "Keep the responses brief and concise, but add a little flare to make them less serious."\
                                        "You should not refer to yourself as a statue most of the time, but as actually being Enzo Ferrari")
        self.activated = True

    async def on_enter(self):
        # Inform the user that the agent is waiting for the wake word
        logger.info(f"Waiting for button press")
        self.activated = False
        led.wakeup()

    def stt_node(self, audio: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(audio, model_settings)

        if not self.activated:
            return None
        
        async def process_stream():
            async for event in parent_stream:
                yield event
        return process_stream()
    
    async def on_user_turn_completed(self, chat_ctx, new_message=None):  
        # Only generate a reply if the wake word was detected  
        if self.activated:  
            # Let the default behavior happen 
            led.think()
            result = await super().on_user_turn_completed(chat_ctx, new_message)
            return result
        # Otherwise, don't generate a reply
        raise StopResponse()
    
    async def user_timeout(self):
        logger.info("User timed out, chat reset")
        self.activated = False
        led.wakeup()
        await self.update_chat_ctx(ChatContext())

    @function_tool()
    async def end_conversation(self) -> None:
        """
        End the conversation when the user signals so.
        """
        await self.session.generate_reply(
            instructions="Tell the user a friendly goodbye, like Enzo Ferrari would. Keep it short"
        )
        self.activated = False
        led.wakeup()
        logger.info("Response completed, waiting button")
        await self.update_chat_ctx(ChatContext())

    def button_callback(self,channel):
        self.activated = not self.activated
        if self.activated:
            async def introduce():
                await self.session.generate_reply(
                    instructions="Greet the user quickly",
                    allow_interruptions=False
                )
            introduce()
            led.listen()
        else:
            led.wakeup()
        logger.info(f'Toggeled activation state, new state is: {str(self.activated)}')
        

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUTTON,GPIO.FALLING,callback= self.button_callback,bouncetime=200)



async def entrypoint(ctx: agents.JobContext):
    agent = AI_Guide()
    agent.setup_gpio()

    session = AgentSession(
        stt=openai.STT(model = "gpt-4o-mini-transcribe"),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(
            model = 'tts-1',
            voice="ash",
            instructions="Speak in a friendly and conversational tone.",
            ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        user_away_timeout=15,
        allow_interruptions=False
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()
    
    @session.on("agent_state_changed")
    def agent_state_changed(event):
        logger.info(f'Agent state event:{event}')
        if event.new_state == 'listening' and agent.activated:
            led.listen()
        elif event.new_state == 'speaking':
            led.speak()


    @session.on("user_state_changed")
    def on_user_state_changed(event):
        if event.new_state == "away" and agent.activated:
            asyncio.create_task(agent.user_timeout())
    

    @session.on('close')
    def on_close(event):
        led.off()
        GPIO.cleanup()
    

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
