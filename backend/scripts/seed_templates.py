"""
Seed 6 starter templates (one per scenario, primary channel each).
Run from the backend/ directory: uv run python scripts/seed_templates.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from sqlmodel import Session, select

from src.lynk.db import engine
from src.lynk.models import Template, TemplateVersion
from src.lynk.models.template import Channel, Scenario

TEMPLATES = [
    {
        "name": "PS Outreach — Cold Email",
        "scenario": Scenario.ps_outreach,
        "channel": Channel.cold_email,
        "subject_template": "Practice School interest — {{ company.name }}",
        "body_template": """\
Hi {{ person.first_name }},

I'm Anmol Sen, a final-year dual-degree student at BITS Pilani Goa (M.Sc. Physics + B.E. EEE,
graduating May 2027). I'm applying for the BITS Practice School (PS) program for the Aug 2026 –
May 2027 cycle and came across {{ company.name }}'s work — particularly {{ person.current_position }}
resonated with my background in ML and physics-informed systems.

A few highlights from my work:
- Face Sentinel: CNN-ViT deepfake detection at 92.74% accuracy
- SAGE: GNN-based GPU anomaly detection with 38% improvement over baselines
- Pulse Ingest: Kafka→Iceberg pipeline in Rust handling millions of events/hour

I'd love to learn whether {{ company.name }} has participated or plans to participate in PS for this cycle.
Even a 10-minute call would be incredibly helpful.

Thank you for your time,
Anmol Sen
BITS Pilani Goa | f20221215@goa.bits-pilani.ac.in
""",
    },
    {
        "name": "Research / GSoC — LinkedIn DM",
        "scenario": Scenario.research_gsoc,
        "channel": Channel.li_dm,
        "subject_template": None,
        "body_template": """\
Hi {{ person.first_name }},

I'm Anmol — a final-year Physics + EEE student at BITS Pilani Goa working at the intersection of
ML and stochastic processes. I'm actively applying for GSoC 2026 (ML4SCI TITAN, CERN-HSF LHCb) and
your work on {{ person.current_position }} caught my attention.

I'd love to hear your perspective on open problems in this space and whether there are ways I could
contribute to your group's work, either through GSoC or independently.

Happy to share more about my projects (GNN anomaly detection, deepfake detection, LLM reliability
benchmarking) if helpful. Would you be open to a quick chat?

Best,
Anmol
""",
    },
    {
        "name": "Referral Request — LinkedIn DM",
        "scenario": Scenario.referral_request,
        "channel": Channel.li_dm,
        "subject_template": None,
        "body_template": """\
Hi {{ person.first_name }},

Hope things are going well at {{ company.name }}! I'm in my final year at BITS Pilani Goa and
actively looking for opportunities in ML engineering / backend engineering for Aug 2026 onwards.

I know {{ company.name }}'s engineering culture well from following your work, and I think my
background (GNNs, production Rust pipelines, LLM systems) could be a good fit.

Would you be open to a quick intro call, or if you're comfortable, passing along my profile to
the relevant team? No pressure at all — I know referrals are a big ask.

Thanks,
Anmol
""",
    },
    {
        "name": "Informational Call — Cold Email",
        "scenario": Scenario.info_call,
        "channel": Channel.cold_email,
        "subject_template": "Quick question about your path at {{ company.name }}",
        "body_template": """\
Hi {{ person.first_name }},

I'm Anmol Sen, a final-year student at BITS Pilani Goa (M.Sc. Physics + B.E. EEE). I came across
your profile and was impressed by your work as {{ person.current_position }} at {{ company.name }}.

I'm navigating career decisions around ML research vs. engineering roles, and your trajectory
seems particularly relevant. Would you be open to a 15-minute call to share your experience?
I'd be respectful of your time and come prepared with specific questions.

Best,
Anmol Sen | f20221215@goa.bits-pilani.ac.in
""",
    },
    {
        "name": "Alumni Outreach — LinkedIn DM",
        "scenario": Scenario.alumni,
        "channel": Channel.li_dm,
        "subject_template": None,
        "body_template": """\
Hi {{ person.first_name }},

Fellow BITSian here — I'm Anmol, currently in my final year at BITS Pilani Goa (Physics + EEE,
graduating May 2027). I came across your profile and noticed you're at {{ company.name }} —
really impressive work.

I'm exploring opportunities in ML engineering and would love to hear about your experience
post-BITS, especially how you made the transition to {{ company.name }}. Would you be open to
a short call sometime?

Thanks,
Anmol
""",
    },
    {
        "name": "Founder / Early-Stage — LinkedIn Connection Note",
        "scenario": Scenario.founder,
        "channel": Channel.li_connection_note,
        "subject_template": None,
        "body_template": "Hi {{ person.first_name }}, love what {{ company.name }} is building. "
        "Physics + ML background, building production ML systems. Would love to connect.",
    },
]


def seed() -> None:
    with Session(engine) as session:
        for tmpl_data in TEMPLATES:
            existing = session.exec(
                select(Template).where(
                    Template.name == tmpl_data["name"],
                )
            ).first()
            if existing:
                print(f"  skip (exists): {tmpl_data['name']}")
                continue

            template = Template(
                name=tmpl_data["name"],
                scenario=tmpl_data["scenario"],
                channel=tmpl_data["channel"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(template)
            session.flush()

            version = TemplateVersion(
                template_id=template.id,
                version=1,
                subject_template=tmpl_data.get("subject_template"),
                body_template=tmpl_data["body_template"],
                notes="Initial seed template",
                created_at=datetime.utcnow(),
            )
            session.add(version)
            session.flush()

            template.active_version_id = version.id
            template.updated_at = datetime.utcnow()
            session.add(template)
            print(f"  created: {tmpl_data['name']}")

        session.commit()
    print("Done.")


if __name__ == "__main__":
    seed()
