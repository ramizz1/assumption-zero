"""Shared example analysis used by both the web interface and CLI."""
from __future__ import annotations

from assumption_zero.schemas import IdeaInput


DEMO_IDEA = IdeaInput(
    name="LegalMind Local",
    description="A privacy-first AI meeting summarizer that runs entirely on-device for small legal firms",
    problem=(
        "Legal professionals have confidential client meetings that cannot be transcribed "
        "using cloud AI tools due to attorney-client privilege and data sovereignty concerns. "
        "Existing tools like Otter.ai send audio to remote servers, creating compliance risks."
    ),
    target_customer="Solo practitioners and small law firms (1-20 attorneys)",
    geography="United States",
    business_model="SaaS subscription per seat, installed locally",
    price="$49/month per attorney",
    founder_skills="Full-stack developer, 5 years experience, some ML background",
    budget="$15,000 runway for 6 months",
    known_competitors="Otter.ai, Fireflies.ai, Whisper (open source), Tactiq",
    additional_context=(
        "Planning to use OpenAI Whisper for transcription and a local Llama model for "
        "summarization. Initial target is solo practitioners who already use case management software."
    ),
)
