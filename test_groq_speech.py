import asyncio

from backend.infrastructure.speech.groq_speech import GroqSpeechToText


async def main():
    with open("voice_test.wav", "rb") as file:
        audio = file.read()

    print(f"Audio size: {len(audio)} bytes")

    speech = GroqSpeechToText()

    text = await speech.transcribe(
        audio=audio,
        filename="voice_test.wav",
    )

    print("\nTranscription:")
    print(text)


if __name__ == "__main__":
    asyncio.run(main())