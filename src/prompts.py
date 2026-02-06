from __future__ import annotations

from .models import ParticipantConfig


def build_system_prompt(participant: ParticipantConfig, meeting_title: str) -> str:
    return (
        f"You are {participant.name}, a participant in the meeting: "
        f'"{meeting_title}".\n\n'
        f"Role: {participant.role}\n"
        f"Personality: {participant.personality}\n"
        f"Responsibility: {participant.description}\n\n"
        "Guidelines:\n"
        "- Stay in character at all times.\n"
        "- Address other participants by name when responding to them.\n"
        "- Be concise and focused. This is a multi-person meeting; keep your "
        "responses to 2-4 paragraphs unless the topic demands more detail.\n"
        "- If you have nothing meaningful to add, say so briefly.\n"
    )


def build_relevance_check_prompt(
    participant_name: str,
    latest_message_author: str,
    latest_message_text: str,
) -> str:
    return (
        f"The following message was just said in the meeting by "
        f"{latest_message_author}:\n\n"
        f'"""\n{latest_message_text}\n"""\n\n'
        f"{participant_name}, do you have something meaningful to contribute "
        "in response? Consider whether your expertise is relevant and whether "
        "you can add a new perspective.\n\n"
        "You MUST respond in EXACTLY this format (two lines only):\n"
        "DECISION: YES\n"
        "SUMMARY: <one-sentence summary of what you want to say>\n\n"
        "Or:\n"
        "DECISION: NO\n"
        "SUMMARY: <one-sentence reason you are passing>\n"
    )


def build_recheck_prompt(
    participant_name: str,
    speaker_name: str,
    speaker_message: str,
) -> str:
    return (
        f"{speaker_name} just said:\n\n"
        f'"""\n{speaker_message}\n"""\n\n'
        f"{participant_name}, given this new message, do you still want to "
        "speak? Only say YES if you have something new and meaningful to add "
        "that hasn't been covered yet.\n\n"
        "You MUST respond in EXACTLY this format (two lines only):\n"
        "DECISION: YES\n"
        "SUMMARY: <one-sentence summary of what you want to say>\n\n"
        "Or:\n"
        "DECISION: NO\n"
        "SUMMARY: <one-sentence reason you are passing>\n"
    )


def build_notes_prompt(conversation_block: str) -> str:
    return (
        "You are a meeting notes assistant. Summarize the following meeting "
        "exchange into 3-5 concise bullet points. Focus on decisions made, "
        "key arguments, action items, and open questions.\n\n"
        "Conversation:\n"
        f'"""\n{conversation_block}\n"""\n\n'
        "Respond with bullet points only, no preamble."
    )
