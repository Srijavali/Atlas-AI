from backend.domain.enums import InteractionType
from backend.domain.models.interaction import IncomingInteraction
from backend.persistence.models.user import OnboardingStatus

from backend.modules.scheduler.reminder_parser import ReminderParser


class CommunicationService:
    """
    Coordinates inbound communication without owning
    platform-specific logic.

    Telegram parsing/adaptation happens before this service.
    Telegram delivery happens after this service.
    """

    def __init__(
        self,
        *,
        user_repository,
        onboarding_repository,
        onboarding_service,
        preprocessing_service,
        media_fetcher=None,
        speech_to_text=None,
        atlas_agent=None,
        scheduler_service=None,
    ):
        self._user_repository = user_repository
        self._onboarding_repository = onboarding_repository
        self._onboarding_service = onboarding_service
        self._preprocessing_service = preprocessing_service
        self._media_fetcher = media_fetcher
        self._speech_to_text = speech_to_text
        self._atlas_agent = atlas_agent

        self._scheduler_service = scheduler_service
        self._reminder_parser = ReminderParser()

    async def handle(
        self,
        interaction: IncomingInteraction,
    ) -> str:
        """
        Process one platform-neutral incoming interaction.

        Returns the text that should eventually be sent back
        through the Communication Layer.
        """

        telegram_user_id = int(interaction.user_id)

        user = await self._user_repository.get_by_telegram_user_id(
            telegram_user_id
        )

        # ---------------------------------------------------------
        # NEW USER
        # ---------------------------------------------------------

        if user is None:
            display_name = (
                interaction.metadata.get("first_name")
                or interaction.metadata.get("username")
            )

            user = await self._user_repository.create_user(
                telegram_user_id=telegram_user_id,
                telegram_username=interaction.metadata.get(
                    "username"
                ),
                display_name=display_name,
            )

            result = await self._onboarding_service.start(
                user.id,
            )

            return result.message

        # Update activity for every known user.
        await self._user_repository.update_last_seen(
            user.id
        )

        # ---------------------------------------------------------
        # /start
        # ---------------------------------------------------------

        if (
            interaction.interaction_type == InteractionType.COMMAND
            and interaction.text
            and interaction.text.strip().lower() == "/start"
        ):
            if user.onboarding_status == OnboardingStatus.COMPLETED:
                return (
                    "Welcome back! 👋\n\n"
                    "You're already set up with Atlas. "
                    "What would you like to do?"
                )

            result = await self._onboarding_service.start(
                user.id,
            )

            return result.message

        # ---------------------------------------------------------
        # ONBOARDING
        # ---------------------------------------------------------

        if user.onboarding_status != OnboardingStatus.COMPLETED:
            session = await self._onboarding_repository.get_by_user_id(
                user.id,
            )

            if session is None:
                result = await self._onboarding_service.start(
                    user.id,
                )

                return result.message

            if not interaction.text:
                return (
                    "I need a text response for this "
                    "onboarding step. 😊"
                )

            result = await self._onboarding_service.handle_response(
                session=session,
                response=interaction.text,
            )

            return result.message

        # =========================================================
        # COMPLETED USER
        # =========================================================

        # ---------------------------------------------------------
        # TEXT
        # ---------------------------------------------------------

        if interaction.interaction_type == InteractionType.TEXT:
            if not interaction.text:
                return "I didn't receive any text. 😊"

            preprocessed = self._preprocessing_service.process_text(
                interaction.text,
            )

            text = preprocessed.text

            # -----------------------------------------------------
            # ONE-TIME REMINDER
            # -----------------------------------------------------

            if self._scheduler_service is not None:
                reminder = self._reminder_parser.parse(text)

                if reminder is not None:
                    try:
                        await self._scheduler_service.schedule_reminder(
                            telegram_user_id=telegram_user_id,
                            message=reminder.reminder_text,
                            delay_seconds=reminder.delay_seconds,
                        )

                    except ValueError as exc:
                        return (
                            "I couldn't schedule that reminder. "
                            f"{str(exc)}"
                        )

                    except RuntimeError:
                        return (
                            "My reminder system isn't available "
                            "right now. Please try again."
                        )

                    delay_text = self._format_delay(
                        reminder.delay_seconds
                    )

                    return (
                        "🔔 Reminder scheduled!\n\n"
                        f"I'll remind you about "
                        f"**{reminder.reminder_text}** "
                        f"in **{delay_text}**.\n\n"
                        "You can continue using Atlas normally "
                        "while I handle the reminder."
                    )

            # -----------------------------------------------------
            # NORMAL ATLAS REQUEST
            # -----------------------------------------------------

            if self._atlas_agent is not None:
                return await self._atlas_agent.intelligent_response(
                    text=text,
                    user_context={},
                )

            return text

        # ---------------------------------------------------------
        # DOCUMENT
        # ---------------------------------------------------------

        if interaction.interaction_type == InteractionType.DOCUMENT:
            if self._media_fetcher is None:
                return (
                    "Multimodal media retrieval is not configured."
                )

            if not interaction.media_reference:
                return (
                    "I received the document, but I couldn't "
                    "access its file data."
                )

            filename = (
                interaction.metadata.get("filename")
                or "document"
            )

            content = await self._media_fetcher.fetch(
                interaction.media_reference
            )

            preprocessed = (
                self._preprocessing_service.process_document(
                    content,
                    filename=filename,
                )
            )

            if self._atlas_agent is not None:
                return await self._atlas_agent.intelligent_response(
                    text=preprocessed.text,
                    user_context={
                        "input_type": "document",
                        "filename": filename,
                    },
                )

            return preprocessed.text

        # ---------------------------------------------------------
        # VOICE
        # ---------------------------------------------------------

        if interaction.interaction_type == InteractionType.VOICE:
            if self._media_fetcher is None:
                return (
                    "Multimodal media retrieval is not configured."
                )

            if not interaction.media_reference:
                return (
                    "I received the voice message, but I couldn't "
                    "access its audio data."
                )

            filename = (
                interaction.metadata.get("filename")
                or "voice.ogg"
            )

            content = await self._media_fetcher.fetch(
                interaction.media_reference
            )

            # -----------------------------------------------------
            # VOICE -> SPEECH TO TEXT
            # -----------------------------------------------------

            if self._speech_to_text is not None:
                transcribed_text = (
                    await self._speech_to_text.transcribe(
                        audio=content,
                        filename=filename,
                    )
                )

                if (
                    not isinstance(transcribed_text, str)
                    or not transcribed_text.strip()
                ):
                    return (
                        "I couldn't understand the voice message. "
                        "Please try speaking again."
                    )

                transcribed_text = transcribed_text.strip()

                # -------------------------------------------------
                # VOICE -> REMINDER
                # -------------------------------------------------

                if self._scheduler_service is not None:
                    reminder = self._reminder_parser.parse(
                        transcribed_text
                    )

                    if reminder is not None:
                        try:
                            await self._scheduler_service.schedule_reminder(
                                telegram_user_id=telegram_user_id,
                                message=reminder.reminder_text,
                                delay_seconds=reminder.delay_seconds,
                            )

                        except ValueError as exc:
                            return (
                                "I couldn't schedule that reminder. "
                                f"{str(exc)}"
                            )

                        except RuntimeError:
                            return (
                                "My reminder system isn't available "
                                "right now. Please try again."
                            )

                        delay_text = self._format_delay(
                            reminder.delay_seconds
                        )

                        return (
                            "🔔 Voice reminder scheduled!\n\n"
                            f"I'll remind you about "
                            f"**{reminder.reminder_text}** "
                            f"in **{delay_text}**."
                        )

                # -------------------------------------------------
                # VOICE -> ATLAS
                # -------------------------------------------------

                if self._atlas_agent is not None:
                    return await self._atlas_agent.intelligent_response(
                        text=transcribed_text,
                        user_context={
                            "input_type": "voice",
                            "filename": filename,
                        },
                    )

                return transcribed_text

            # -----------------------------------------------------
            # FALLBACK AUDIO PREPROCESSING
            # -----------------------------------------------------

            preprocessed = (
                self._preprocessing_service.process_audio(
                    content,
                    filename=filename,
                )
            )

            if self._atlas_agent is not None:
                return await self._atlas_agent.intelligent_response(
                    text=preprocessed.text,
                    user_context={
                        "input_type": "audio",
                        "filename": filename,
                    },
                )

            return preprocessed.text

        # ---------------------------------------------------------
        # IMAGE
        # ---------------------------------------------------------

        if interaction.interaction_type == InteractionType.IMAGE:
            if self._media_fetcher is None:
                return (
                    "Multimodal media retrieval is not configured."
                )

            if not interaction.media_reference:
                return (
                    "I received the image, but I couldn't "
                    "access its file data."
                )

            filename = (
                interaction.metadata.get("filename")
                or "image"
            )

            content = await self._media_fetcher.fetch(
                interaction.media_reference
            )

            try:
                preprocessed = (
                    self._preprocessing_service
                    .process_image_for_vision(
                        content,
                    )
                )

            except Exception:
                return (
                    "I received the image, but I couldn't "
                    "understand its visual content."
                )

            if self._atlas_agent is not None:
                return await self._atlas_agent.intelligent_response(
                    text=preprocessed.text,
                    user_context={
                        "input_type": "image",
                        "filename": filename,
                    },
                )

            return preprocessed.text

        return (
            "I received your message, but I don't support "
            "that interaction type yet."
        )

    @staticmethod
    def _format_delay(
        delay_seconds: int,
    ) -> str:
        """
        Convert seconds into a human-readable delay.
        """

        if delay_seconds < 60:
            return (
                f"{delay_seconds} second"
                + ("s" if delay_seconds != 1 else "")
            )

        if delay_seconds < 3600:
            minutes = delay_seconds // 60

            return (
                f"{minutes} minute"
                + ("s" if minutes != 1 else "")
            )

        hours = delay_seconds // 3600

        return (
            f"{hours} hour"
            + ("s" if hours != 1 else "")
        )