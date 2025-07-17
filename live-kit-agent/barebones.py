from dotenv import load_dotenv

from livekit import agents,api
from livekit.agents import AgentSession, Agent, RoomInputOptions,get_job_context, function_tool,RunContext
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)

from livekit.plugins.turn_detector.english import EnglishModel



import ssl
import certifi
import aiohttp

load_dotenv()

async def hangup_call():
    ctx = get_job_context()
    if ctx is None:
        # Not running in a job context
        return
    
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(
            room=ctx.room.name,
        )
    )

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")

    @function_tool
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        # let the agent finish speaking
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()

        await hangup_call()


async def entrypoint(ctx: agents.JobContext):
    # ssl_context = ssl.create_default_context(cafile=certifi.where())

    # # aiohttp session created safely inside the event loop
    # aiohttp_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))

    session = AgentSession(
        stt=openai.STT(model = 'whisper-1'),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(model = 'tts-1',
            voice="ash"
            ),
        vad=silero.VAD.load(),
        turn_detection=EnglishModel(),
        user_away_timeout=5
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )

    @session.on("user_state_changed")
    def on_user_state_changed(event):
        if event.new_state == "away":
            print(event)
            # asyncio.run(hangup_call()
            # )



if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))