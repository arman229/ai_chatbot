import chainlit as cl
from dotenv import load_dotenv
from typing import cast
import chainlit as cl
import os
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set. Please ensure it is defined in your .env file."
    )


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Startup pitch writing.",
            message="Help me write a compelling pitch for my startup idea. Start by asking what my product does, who it helps, and why it's unique.",
            icon="/public/pitch.svg",
        ),
        cl.Starter(
            label="Travel itinerary planner.",
            message="Can you plan a 5-day travel itinerary for a relaxing trip to Japan with a mix of culture, nature, and food?",
            icon="/public/travel.svg", 
        ),
    ]


@cl.on_chat_start
async def start():
    external_client = AsyncOpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash", openai_client=external_client
    )

    config = RunConfig(
        model=model, model_provider=external_client, tracing_disabled=True
    )
    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)
    agent: Agent = Agent(
        name="Assistant", instructions="You are a helpful assistant", model=model
    )
    cl.user_session.set("agent", agent)

    # await cl.Message(content="Welcome to the AI Assistant! How can I help you today?").send()


@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("chat_history") or []
    history.append({"role": "user", "content": message.content})
    msg = cl.Message(content="")
    await msg.send()

    agent: Agent = cast(Agent, cl.user_session.get("agent"))
    config: RunConfig = cast(RunConfig, cl.user_session.get("config"))

    try:
        result = Runner.run_streamed(agent, history, run_config=config)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                token = event.data.delta
                await msg.stream_token(token)
        history.append({"role": "assistant", "content": msg.content})
        cl.user_session.set("chat_history", history)

    except Exception as e:
        await msg.update(content=f"Error: {str(e)}")
        print(f"Error: {str(e)}")
