from __future__ import annotations

import json
import logging

import anthropic

from ..config import settings
from ..models.person import Person
from ..models.template import Channel, TemplateVersion

logger = logging.getLogger(__name__)

USER_BIO = """
You are drafting outreach messages on behalf of Anmol Sen, a final-year dual-degree student
at BITS Pilani Goa (M.Sc. Physics + B.E. EEE, graduating May 2027). His core differentiator
is the Physics + ML combination.

Background:
- Languages: Python, C, C++, Java, TypeScript, SQL
- Frameworks: PyTorch, TensorFlow/Keras, PyGeometric, OpenCV, FastAPI, React
- Tools: Git, Docker, Linux, ROS2, SLAM

Key projects:
- Face Sentinel: CNN-ViT hybrid deepfake detection, 92.74% accuracy, 0.9787 AUC (Celeb-DF v2)
- SAGE: GNN-based distributed GPU anomaly detection, 38% improvement over rule-based baselines
- AI Crucible: adversarial multi-agent reasoning engine on LangGraph, 7-agent red team
- Axiom: LLM reliability evaluation engine, async multi-model benchmarking across 7 providers
- Pulse Ingest: Kafka → Iceberg pipeline in Rust, millions of events/hour
- Signal SQL: Arrow-native SQL engine with MVCC, passes 100% SQLite sqllogictest suite
- Project Kratos: Mars rover full autonomy stack (ROS2, SLAM, LiDAR)
- IssueOps: serverless GitHub triage platform, published on GitHub Marketplace

Experience:
- Research Intern, SONAm Lab BITS Goa (Aug 2025–present): ML for anomalous diffusion, 88.96% macro-F1
- Backend Engineering Intern, HealthSmart (Dec 2025–Jan 2026): 20+ REST APIs, JWT auth, audit logging
- ITS Technology Intern, West Bengal Transport Corporation (May–Jul 2024): Android ticketing system

Research interests: anomalous diffusion, stochastic processes, GNNs, deepfake detection, LLM reliability
Active GSoC 2026 applicant (ML4SCI TITAN, CERN-HSF LHCb)
Primary email: f20221215@goa.bits-pilani.ac.in
"""

CHANNEL_INSTRUCTIONS = {
    Channel.li_connection_note: (
        "This is a LinkedIn CONNECTION REQUEST NOTE. "
        "Hard limit: 300 characters including spaces. Count carefully. "
        "Be concise, specific, and personal. No fluff. Return subject as null."
    ),
    Channel.li_dm: (
        "This is a LinkedIn DIRECT MESSAGE to an existing connection. "
        "2–4 short paragraphs. Conversational tone, not formal. Return subject as null."
    ),
    Channel.cold_email: (
        "This is a COLD EMAIL. "
        "Include a compelling subject line (≤60 chars). "
        "3–5 short paragraphs. Professional but warm. Include a clear single call to action."
    ),
}


def _pick_model(person: Person) -> str:
    if person.priority >= 2:
        return settings.claude_model_high_priority
    return settings.claude_model_default


def generate_message(
    person: Person,
    template_version: TemplateVersion,
    scenario_context: str,
    channel: Channel,
    company_name: str | None = None,
    custom_instructions: str | None = None,
) -> dict[str, str | None]:
    """
    Returns {"subject": str | None, "body": str}.
    Raises RuntimeError if API key is missing or response cannot be parsed.
    """
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    model = _pick_model(person)

    system_content = (
        USER_BIO
        + "\n\n---\n\n"
        + "SCENARIO: "
        + scenario_context
        + "\n\n"
        + CHANNEL_INSTRUCTIONS[channel]
        + "\n\n"
        + "TEMPLATE (fill in personalization, keep the structure):\n"
        + template_version.body_template
    )
    if custom_instructions:
        system_content += "\n\nADDITIONAL INSTRUCTIONS:\n" + custom_instructions

    person_info = {
        "full_name": person.full_name,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "headline": person.headline,
        "current_position": person.current_position_title,
        "company": company_name,
        "location": person.location,
    }

    user_message = (
        "Draft the message for this person:\n"
        + json.dumps(person_info, indent=2)
        + "\n\nRespond with ONLY valid JSON: "
        + '{"subject": "..." or null, "body": "..."}'
        + "\nNo markdown, no extra text."
    )

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system_content,
                "cache_control": {"type": "ephemeral"},  # type: ignore[dict-item]
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    first_block = response.content[0]
    if not hasattr(first_block, "text"):
        raise RuntimeError(f"Unexpected response block type: {type(first_block)}")
    raw: str = first_block.text.strip()  # type: ignore[union-attr]
    try:
        result: dict[str, str | None] = json.loads(raw)
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise RuntimeError(f"Claude returned non-JSON response: {raw[:200]}")
        result = json.loads(match.group())

    body: str | None = result.get("body", "")
    if channel == Channel.li_connection_note and body and len(body) > 300:
        logger.warning("LI connection note exceeded 300 chars (%d), truncating", len(body))
        body = body[:297] + "..."
        result["body"] = body

    logger.info("Generated %s message for %s using %s", channel, person.full_name, model)
    return result
