# LinkedIn Outreach & Content System — Build Brief

## Project Context

I'm building a semi-automated LinkedIn + email outreach + content system for my own professional use. This is a **personal productivity tool**, not a SaaS product. I'm a final-year dual-degree student at BITS Pilani Goa (M.Sc. Physics + B.E. EEE) targeting Practice School (PS) internship placements for Aug 2026 – May 2027, plus ongoing professional networking for GSoC, research roles, and longer-term career opportunities.

Primary email for outreach: `f20221215@goa.bits-pilani.ac.in` (BITS college email — needs to remain valid through May 2027).

**My technical background** (use this as system context for personalization in every generated message):
- Dual degree: M.Sc. Physics + B.E. EEE, BITS Pilani Goa, graduating May 2027
- Physics + ML combination as core differentiator
- Languages: Python, C, C++, Java, TypeScript, SQL
- Frameworks: PyTorch, TensorFlow/Keras, PyGeometric, OpenCV, FastAPI, React
- Tools: Git, Docker, Linux, ROS2, SLAM

Key projects:
- Face Sentinel: CNN-ViT hybrid deepfake detection, 92.74% accuracy, 0.9787 AUC on Celeb-DF v2
- SAGE: GNN-based distributed GPU anomaly detection, 38% improvement over rule-based baselines
- AI Crucible: adversarial multi-agent reasoning engine on LangGraph with 7-agent red team
- Axiom: LLM reliability evaluation engine, async multi-model benchmarking across 7 providers
- Pulse Ingest: Kafka → Iceberg data pipeline in Rust, millions of events/hour
- Signal SQL: Arrow-native SQL engine with MVCC, passes 100% SQLite sqllogictest suite
- Project Kratos: Mars rover full autonomy stack (ROS2, SLAM, LiDAR)
- IssueOps: serverless GitHub triage platform, published on GitHub Marketplace

Experience:
- Research Intern, SONAm Lab BITS Goa (Aug 2025–present): ML for anomalous diffusion trajectory classification, 88.96% macro-F1
- Backend Engineering Intern, HealthSmart (Dec 2025–Jan 2026): 20+ REST APIs, JWT auth, audit logging
- ITS Technology Intern, West Bengal Transport Corporation (May–Jul 2024): Android ticketing system across 80+ buses

Research interests: anomalous diffusion, stochastic processes, GNNs, deepfake detection, LLM reliability
Active GSoC 2026 applicant (ML4SCI TITAN, CERN-HSF LHCb)

**Build philosophy:**
- Token-cost-aware at every design decision
- Free tools only (no paid APIs like Hunter.io, Apollo paid tier)
- Claude API for text generation, Gemini API free tier as secondary
- Semi-automated: agent does all thinking, I click to send (zero LinkedIn ban risk)

---

## System Overview

A unified dashboard with three modules:

1. **People DB + Pipeline** — CRM for outreach targets
2. **Outreach Engine** — multi-channel message generation + tracking
3. **Content Studio** — LinkedIn post/carousel generation

Plus shared infrastructure: email finder, tracking pixel server, rate limiting, analytics.

---

## Module 1: People DB + Pipeline

### Data sources
- **Import**: LinkedIn connections CSV (~10.5k rows — has name, LinkedIn URL, company, position, connected date; most missing email)
- **Manual add**: single-person entry
- **Target discovery**: hybrid flow — I paste a company name, system searches company website + LinkedIn for relevant people (HR, engineers, founders, alumni), presents candidates, I confirm which to add
- **PS historical lists**: import xlsx files of past PS company lists to pre-populate a dedicated PS station DB (will provide files later)

### Dedup on import
Same person listed multiple times (job changes) should be merged — keep latest position, retain history.

### Filtering & tagging
- Filter by: company, industry, position keywords, location, connection date, stage, campaign
- Free-text tags (user-defined)
- **Notes field** per person (free-text for context: "met at X", "referred by Y", etc.)

### Pipeline stages
```
Not contacted
  → Contacted (LinkedIn / email / both)
    → Opened (no reply)
      → Replied
        → Call/Interview scheduled
          → Offer / Rejected
    → Bounced / Wrong person
  → Cold (no response after all follow-ups)
    → Recyclable after 90 days
  → Opted out (never contact again — permanent)
```

### Bulk actions
Select N people → apply: change stage, assign campaign, add tag, mark priority, export subset.

### PS company DB (first-class entity, not just tags)
- Station name, company, domain, historical years on PS list
- Typical roles, technologies, location
- Application deadline (per year)
- Priority tier (based on my fit)
- Linked to People DB entries at that company

---

## Module 2: Outreach Engine

### Three target pools (can overlap per person)
- **Existing connections** → DM on LinkedIn directly
- **New LinkedIn targets** → connection request note → DM after accept
- **Email-only** → cold email

### Email finder (priority order)
1. Already in CSV / DB
2. **Company domain pattern from own DB** (learned from confirmed sends)
3. Domain permutation guesser (firstname.lastname, firstname, f.lastname, etc.)
4. Hunter.io free tier (25/month)
5. Apollo.io free tier (50/month)
6. Skrapp.io free tier (150/month)
7. LinkedIn "Contact Info" section (manual fallback)

### Company domain pattern learning
When an email is confirmed valid (sent, no bounce, ideally opened), extract pattern and save to company DB:
```
infosys.com → firstname.lastname → High confidence (N samples)
startup.io → firstname → Low confidence (1 sample)
```
Next time we target anyone at that company, pattern DB is checked first. Confidence rises with more confirmed samples; bounces lower it.

### SMTP verification before send
Run a lightweight SMTP handshake (`pyIsEmail` or equivalent) on every address before sending to catch bad emails and protect sender reputation.

### Message generation
Three message types:
- **LinkedIn connection request note** (300 char limit)
- **LinkedIn DM** (for existing connections)
- **Cold email** (subject + body)

**Hybrid template + generation approach:**
- Base templates per scenario: PS outreach, research/GSoC, referral request, informational call, alumni reach-out, founder/early-startup
- Claude fills personalization: their role, company, shared background, specific project relevance
- Each template has version history (v1, v2, v3) for A/B testing

### A/B testing
- Per campaign, assign people to template variants
- Track: open rate, click rate, reply rate per variant
- Minimum 30-50 sends per variant before declaring a winner
- Auto-promote winning variant for remaining targets in campaign

### Multi-channel orchestration per person
Dashboard shows one row per person with all channels visible:
```
| Person | LinkedIn status | Email status | Last touch | Next action |
```

---

## Module 3: Email Tracking & Follow-ups

### Tracking infrastructure (self-hosted, free)
- Tiny Flask/FastAPI app on Railway or Render free tier
- Endpoints:
  - `/pixel/<message_id>.png` → 1x1 transparent pixel, logs open timestamp
  - `/click/<message_id>/<link_id>` → redirects to target URL, logs click
- Every outgoing email gets pixel + wrapped links injected automatically
- Data flows back into main DB

### Bounce detection
Parse bounce notifications from Gmail → mark address invalid → decrement company pattern confidence → try next permutation.

### Follow-up logic
```
Email sent
  ↓
Day 3: opened, no reply → Follow-up A (gentle nudge, references original)
Day 3: not opened     → Follow-up B (different subject, re-engage angle)
  ↓
Day 7: still silent   → Follow-up C (final bump)
  ↓
No response → mark Cold → recyclable after 90 days with fresh angle
Reply received → pause ALL follow-ups, surface to active queue
```
Max 2 follow-ups per cycle (so 3 total touches: initial + 2 FUs).

### Opt-out handling
- Auto-detect reply keywords: "not interested", "remove", "unsubscribe", "stop contacting", etc.
- Move to **Opted out** stage (permanent, not recyclable)
- Suppress from all future campaigns
- Surface to me for manual review before permanent blacklist

---

## Module 4: Content Studio

### Formats supported
- **Text posts** (primary, highest ROI for early-career)
- **Image posts** (text + single visual)
- **Carousels** (multi-slide PDF — LinkedIn renders PDF as swipeable cards)

### Content generation
- Topic ideation from my positioning (Physics + ML + production systems)
- Drafts from a one-line prompt ("write about GSoC proposal progress")
- Hook variants, formatting (line breaks, bullets), relevant hashtags
- Tailored to my existing LinkedIn tone/voice (to be calibrated early)

### Carousels — programmatic PDF
- Claude generates: title, per-slide content, visual structure (bullet / quote / chart / step)
- Python renders to styled PDF (reportlab / weasyprint / similar — evaluate during build)
- Consistent typography, color palette, layout templates
- I upload the PDF directly to LinkedIn

### Images for posts
- Evaluate during build: Gemini Imagen API (free tier), Pollinations.ai (no key), HuggingFace FLUX
- Decide based on quality + reliability + rate limits

### Content calendar
- 3x/week default cadence
- Calendar view with copy-ready posts
- LinkedIn has no free posting API → posting is manual but the dashboard makes it a 30-second copy-paste
- **Post history tracking** — store what's been posted to prevent topic/hook repetition
- A/B testing on hooks for posts too (nice-to-have)

---

## Shared Infrastructure

### Rate limiting (hard-coded guardrails)
- **Email**: 50–80/day max, randomized send times, respects Gmail SMTP 500/day ceiling
- **LinkedIn connection requests**: ~90/week cap (buffer below LinkedIn's ~100/week soft limit), spread ~15/day across 6 days
- **LinkedIn DMs**: no strict limit but pace reasonably (~30–50/day)
- System blocks sends that would exceed caps, queues for next window

### Email sending
- Gmail SMTP via BITS email (`f20221215@goa.bits-pilani.ac.in`)
- App password auth
- Every email: pixel injected, links wrapped, threading preserved

### Analytics layer
Dashboard view with:
- Campaign-level metrics: open rate, click rate, reply rate
- Template variant comparison (A/B outcomes)
- Best-performing subject lines
- DM vs email conversion rates
- Pipeline funnel view (how many dropped at each stage)
- Per-company response rates (which companies are actually responsive)

### Token cost control
- Target discovery results cached per company (research TCS once, reuse for all TCS contacts)
- Claude only invoked on explicit "generate" click, never background-auto
- Low-priority targets use lighter prompts / cheaper model tier
- Template-first approach means Claude fills gaps, not whole-email generation from scratch

---

## Tech Stack (proposed — finalize at start of build)

- **Backend**: Python (FastAPI)
- **Database**: SQLite (local, single-user, zero-ops)
- **Frontend**: React or HTMX + Tailwind (decide based on complexity needs)
- **LLM**: Anthropic Claude API (primary), Gemini API (free tier, secondary)
- **Email**: Gmail SMTP via smtplib
- **Tracking server**: separate tiny FastAPI app on Railway/Render free tier
- **Scheduling**: APScheduler or cron
- **CSV/xlsx parsing**: pandas, openpyxl
- **PDF generation**: reportlab or weasyprint (evaluate)
- **Email verification**: pyIsEmail / custom SMTP check
- **Deployment**: local-first (runs on my machine), tracking server is the only hosted component

---

## Suggested Build Phases

**Phase 1 — Foundation (MVP)**
- DB schema + SQLite setup
- CSV import with dedup
- Basic dashboard (list view, filters, notes, tags)
- Manual person add

**Phase 2 — Outreach core**
- Template system + scenarios
- Claude API integration for message generation
- Gmail SMTP send with tracking pixel
- Tracking pixel server deployed
- Basic follow-up scheduler (time-based only, no smart logic yet)

**Phase 3 — Smart features**
- Email finder pipeline (all 7 strategies)
- Company domain pattern learning + storage
- Bounce detection + pattern confidence updates
- Reply detection → pipeline stage transition
- Opt-out detection

**Phase 4 — Rate limiting & safety**
- Daily/weekly caps enforced
- Send queue with randomization
- SMTP pre-send verification

**Phase 5 — A/B + analytics**
- Template versioning
- Campaign-level A/B assignment
- Analytics dashboard

**Phase 6 — Content Studio**
- Post drafting
- Post history
- Calendar view
- Carousel PDF generation

**Phase 7 — Target discovery**
- Company-name-in → candidates-out flow
- PS historical xlsx import (I'll provide files)
- PS station DB

---

## Open Decisions to Make During Build

1. Frontend framework (React vs HTMX — pick based on interactivity needs)
2. PDF carousel library (test 2–3, pick based on output quality)
3. Image gen service (benchmark Gemini Imagen vs Pollinations vs FLUX)
4. Exact prompt structure for each scenario template (will iterate)
5. Tracking server hosting choice (Railway vs Render — pick based on cold-start behavior)

---

## What I Want From You (Claude Code)

- Start with Phase 1, get a working MVP end-to-end before expanding
- Clean, commented code — I want to understand and modify it
- Git-initialized repo with sensible commit structure
- `.env.example` for all secrets (Claude API key, Gmail app password, etc.)
- README with setup + run instructions
- Ask me before making any non-obvious architectural decision
- Flag when something will meaningfully impact token usage
- Don't over-engineer — this is single-user, local, simple is better

When you're ready, propose the Phase 1 file structure and let's confirm before you start writing code.
