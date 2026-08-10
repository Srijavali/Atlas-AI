import asyncio

from backend.infrastructure.llm import GroqRouter
from backend.modules.brain.service import AtlasAgent


async def main():

    agent = AtlasAgent(
        llm=GroqRouter()
    )

    tests = [
        "What is NVIDIA's current stock price?",
        "What was NVIDIA's latest reported revenue?",
        "What is an LLM?",
    ]

    for question in tests:

        print("\n" + "=" * 70)
        print("USER:", question)
        print("=" * 70)

        response = await agent.intelligent_response(
            text=question
        )

        print("ATLAS:")
        print(response)


if __name__ == "__main__":
    asyncio.run(main())