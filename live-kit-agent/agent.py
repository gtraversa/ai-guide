from dotenv import load_dotenv
import asyncio
import logging

from livekit import agents,api
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, get_job_context
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)

from livekit.plugins.turn_detector.english import EnglishModel
from livekit.agents.llm import ChatContext

load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

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

    async def user_timeout(self):
        # if self.wake_word_detected:
        #     self.wake_word_detected = False
        logger.info("User timed out, chat reset")
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
        user_away_timeout=1,
    )

    async def shutdown_cleanup():
        print("shutdown hook")
        return
    
    ctx.add_shutdown_callback(shutdown_cleanup)

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
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))