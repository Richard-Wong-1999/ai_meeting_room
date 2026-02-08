import asyncio
import sys
from datetime import datetime

from .app import MeetingApp
from .config import require_api_key
from .conversation_storage import ConversationData, SessionData, generate_session_id
from .main_menu import show_main_menu
from .model_manager import get_default_models
from .models import AppConfig, MeetingSettings, NotesSummarizerConfig, PoeConfig
from .setup_participants import SetupResult, run_participant_setup
from .splash import display_splash_screen


async def async_main() -> None:
    """Main entry point with menu-driven setup flow."""
    api_key = require_api_key()

    # Display splash screen
    display_splash_screen(duration=3.0)

    try:
        while True:
            # Show main menu
            action, meeting_config, model_settings, session_data = show_main_menu()

            if action == 'quit':
                return

            elif action == 'start_new':
                # New meeting: Run participant design
                available_models = (
                    model_settings.available_models
                    if model_settings.available_models
                    else get_default_models()
                )

                result, participants = await run_participant_setup(
                    meeting_config,
                    api_key,
                    available_models,
                    model_settings.planning_assistant_model
                )

                if result == SetupResult.SUCCESS and participants:
                    # Create session ID and config
                    session_id = generate_session_id()
                    config = AppConfig(
                        meeting=MeetingSettings(
                            title=meeting_config.title,
                            max_rounds_per_turn=meeting_config.max_rounds_per_turn,
                            relevance_timeout_seconds=meeting_config.relevance_timeout_seconds,
                            response_timeout_seconds=meeting_config.response_timeout_seconds,
                        ),
                        poe=PoeConfig(),
                        participants=participants,
                        notes_summarizer=NotesSummarizerConfig(model=model_settings.notes_model),
                    )

                    # Create initial session data
                    initial_session = SessionData(
                        session_id=session_id,
                        title=meeting_config.title,
                        created_at=datetime.utcnow().isoformat(),
                        updated_at=datetime.utcnow().isoformat(),
                        config=config,
                        conversation=ConversationData()
                    )

                    # Launch the application
                    await run_meeting(config, api_key, session_id, initial_session)

                elif result == SetupResult.GO_BACK:
                    continue
                else:  # SetupResult.CANCELLED
                    print("\n設定已取消。")
                    return

            elif action == 'load_conversation':
                # Load existing conversation
                if session_data:
                    await run_meeting(
                        session_data.config,
                        api_key,
                        session_data.session_id,
                        session_data
                    )

    except KeyboardInterrupt:
        print("\n\n再見！\n")


async def run_meeting(
    config: AppConfig,
    api_key: str,
    session_id: str,
    session_data: SessionData
) -> None:
    """Run the meeting application.

    Args:
        config: Meeting configuration
        api_key: POE API key
        session_id: Unique session ID
        session_data: Complete session data (for save/restore)
    """
    app = MeetingApp(config, api_key, session_id, session_data)
    await app.run_async()


def main() -> None:
    """Entry point wrapper."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
