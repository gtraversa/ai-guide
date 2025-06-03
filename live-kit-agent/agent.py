from dotenv import load_dotenv

from livekit import agents,api
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, get_job_context
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)

from livekit.plugins.turn_detector.english import EnglishModel

load_dotenv()

# Initial context
# By default, each AgentSession begins with an empty chat context. You can load user or task-specific data into the agent's 
# context before connecting to the room and starting the session. For instance, this agent greets the user by name based on the job metadata.


class AI_Guide(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a statue of Enzo Ferrari in a museum. Guests will be asking you questions regarding yourself," \
                                        " your life, the history of Ferrari. Guests will also be asking you general questions unrelated to yourself." \
                                        "Keep the responses brief and concise, but add a little flare to make them less serious.")

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="Greet the user like Enzo Ferrari would, in a friendly way."
        )

    @function_tool()
    async def end_call(self) -> None:
        """
        End the conversation when the user signals so.
        """
        await self.session.generate_reply(
            instructions="Tell the user a friendly goodbye, like Enzo Ferrari would."
        )
        job_ctx = get_job_context()
        job_ctx.shutdown(reason="Session ended")
        #await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-4.1"),
        tts=openai.TTS(),
        vad=silero.VAD.load(),
        turn_detection=EnglishModel(),
    )

    async def shutdown_cleanup():
        print("shutdown hook")
        return
    
    ctx.add_shutdown_callback(shutdown_cleanup)

    await session.start(
        room=ctx.room,
        agent=AI_Guide(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))