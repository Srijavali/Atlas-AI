import asyncio

from backend.modules.communication.telegram.parser import TelegramParser
from backend.modules.communication.telegram.adapter import TelegramAdapter
from backend.modules.communication.service import CommunicationService
from backend.modules.preprocessing.service import PreprocessingService
from backend.modules.preprocessing.text.normalizer import TextNormalizer
from backend.modules.preprocessing.documents.document_processor import (
    DocumentProcessor,
)


class FakeMediaFetcher:
    async def fetch(self, file_id: str) -> bytes:
        assert file_id == "test-document-file"

        return b"""
        Atlas AI Financial Report

        Revenue: $81.6 billion
        Net Income: $58.3 billion
        Diluted EPS: $2.39

        This document is being used to test the
        Telegram document preprocessing flow.
        """


class FakeUserRepository:
    async def get_by_telegram_user_id(self, telegram_user_id):
        class User:
            id = 1
            onboarding_status = "COMPLETED"

        return User()

    async def update_last_seen(self, user_id):
        pass


class FakeOnboardingRepository:
    pass


class FakeOnboardingService:
    pass


async def main():
    parser = TelegramParser()
    adapter = TelegramAdapter()

    preprocessing_service = PreprocessingService(
        text_normalizer=TextNormalizer(),
        image_processor=None,
        ocr_processor=None,
        vision_processor=None,
        document_processor=DocumentProcessor(),
        speech_processor=None,
    )

    communication_service = CommunicationService(
        user_repository=FakeUserRepository(),
        onboarding_repository=FakeOnboardingRepository(),
        onboarding_service=FakeOnboardingService(),
        preprocessing_service=preprocessing_service,
        media_fetcher=FakeMediaFetcher(),
    )

    telegram_update = {
        "update_id": 5001,
        "message": {
            "message_id": 9001,
            "from": {
                "id": 123456,
                "username": "sri",
                "first_name": "Sri",
            },
            "chat": {
                "id": 123456,
            },
            "document": {
                "file_id": "test-document-file",
                "file_name": "financial_report.txt",
                "mime_type": "text/plain",
            },
        },
    }

    parsed = parser.parse(telegram_update)

    print("\nParsed Telegram update:")
    print(parsed)

    interaction = adapter.adapt(parsed)

    print("\nAdapted interaction:")
    print(interaction)

    response = await communication_service.handle(
        interaction
    )

    print("\nPreprocessed document text:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())