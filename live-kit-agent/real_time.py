from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, RoomOutputOptions,function_tool
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)
import sys

from openai.types.beta.realtime.session import TurnDetection
from livekit.agents.llm import ChatContext
import asyncio

import RPi.GPIO as GPIO

BUTTON = 17

def button_callback(channel):
    print("Button pressed!")

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BUTTON, GPIO.FALLING, callback=button_callback, bouncetime=200)

def cleanup_gpio():
    GPIO.cleanup()

load_dotenv()


class AI_Guide(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a statue of Enzo Ferrari in a museum. Guests will be asking you questions regarding yourself," \
                                    " your life, the history of Ferrari. Guests will also be asking you general questions unrelated to yourself." \
                                    "Keep the responses brief and concise, but add a little flare to make them less serious.")


    @function_tool()
    async def end_conversation(self) -> None:
        """
        End the conversation when the user signals so.
        """
        await self.session.generate_reply(
            instructions="Tell the user a friendly goodbye, like Enzo Ferrari would. Keep it short"
        )
        cleanup_gpio()
        sys.exit()
        await self.update_chat_ctx(ChatContext())

    async def user_timeout(self):
        await self.update_chat_ctx(ChatContext())


async def entrypoint(ctx: agents.JobContext):
    setup_gpio()
    agent = AI_Guide()

    realtime_llm = openai.realtime.RealtimeModel(
        voice="ash",
        turn_detection=TurnDetection(
            type="server_vad",
            threshold=0.5,
            prefix_padding_ms=300,
            silence_duration_ms=500,
            create_response=True,
            interrupt_response=False,
        )
        # input_audio_transcription={
        #     "language": "en"
        # }
    )
    session = AgentSession(
        llm=realtime_llm,
        user_away_timeout=10,
        allow_interruptions=False
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await ctx.connect()

    @session.on("user_state_changed")
    async def on_user_state_changed(event):
        if event.new_state == "away":
            print(event)
            # asyncio.create_task(agent.user_timeout())
            print(f"\nAgent Session ended for inactivity")
            print("=" * 20)
            print("Chat History:")
            for item in session.history.items:
                if item.type == "message":
                    text = f"{item.role}: {item.text_content}"
                    if item.interrupted:
                        text += " (interrupted)"
                    print(text)
            print("=" * 20)
            await ctx.room.disconnect()


if __name__ == "__main__":
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    finally:
        cleanup_gpio()