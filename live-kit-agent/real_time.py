from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions,function_tool
from livekit.plugins import (
    openai,
    noise_cancellation,
)
from livekit.agents.llm import ChatContext

load_dotenv()


class Assistant(Agent):
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
        await self.update_chat_ctx(ChatContext())


async def entrypoint(ctx: agents.JobContext):
  
    realtime_llm = openai.realtime.RealtimeModel(
        voice="ash",
    )
    session = AgentSession(
        llm=realtime_llm
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


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))