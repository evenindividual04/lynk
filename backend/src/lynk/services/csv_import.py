from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd
from sqlmodel import Session, select

from ..models.company import Company
from ..models.person import Person, Position, Source, Stage
from ..services.dedup import normalize_linkedin_url

EXPECTED_COLUMNS = {"First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"}
DATE_FORMATS = ["%d %b %Y", "%Y-%m-%d", "%m/%d/%Y"]


@dataclass
class ImportResult:
    imported: int = 0
    merged: int = 0
    skipped: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)


def _parse_date(raw: str) -> date | None:
    if not raw or str(raw).strip().lower() in ("", "nan", "none"):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(str(raw).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _find_header_row(lines: list[str]) -> int:
    """LinkedIn CSVs have 2-3 blank/notes lines before the actual header."""
    for i, line in enumerate(lines):
        if "First Name" in line and "Last Name" in line:
            return i
    return 0


def _get_or_create_company(session: Session, name: str) -> Company:
    stmt = select(Company).where(Company.name == name)
    company = session.exec(stmt).first()
    if not company:
        company = Company(name=name)
        session.add(company)
        session.flush()
    return company


def import_csv(file_bytes: bytes, session: Session) -> ImportResult:
    result = ImportResult()

    # Decode with BOM handling
    try:
        content = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = file_bytes.decode("latin-1")

    lines = content.splitlines()
    header_row = _find_header_row(lines)
    csv_content = "\n".join(lines[header_row:])

    try:
        df = pd.read_csv(io.StringIO(csv_content))
    except Exception as exc:
        result.errors.append({"row": "N/A", "error": f"Failed to parse CSV: {exc}"})
        return result

    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        result.errors.append({"row": "header", "error": f"Missing columns: {missing}"})
        return result

    for idx, row in df.iterrows():
        row_num = str(int(idx) + header_row + 2)  # type: ignore[arg-type]
        try:
            raw_url = str(row.get("URL", "")).strip()
            if not raw_url or raw_url.lower() == "nan":
                result.skipped += 1
                continue

            try:
                linkedin_url = normalize_linkedin_url(raw_url)
            except ValueError as exc:
                result.errors.append({"row": row_num, "error": str(exc)})
                result.skipped += 1
                continue

            first_name = str(row.get("First Name", "")).strip()
            last_name = str(row.get("Last Name", "")).strip()
            full_name = f"{first_name} {last_name}".strip()
            email = str(row.get("Email Address", "")).strip() or None
            company_name = str(row.get("Company", "")).strip() or None
            position_title = str(row.get("Position", "")).strip() or None
            connected_date = _parse_date(str(row.get("Connected On", "")))

            # Look up or create company
            company: Company | None = None
            if company_name:
                company = _get_or_create_company(session, company_name)

            existing = session.exec(select(Person).where(Person.linkedin_url == linkedin_url)).first()

            if existing:
                # Merge: archive current position, update fields
                if existing.current_position_title and (
                    existing.current_position_title != position_title
                    or existing.current_company_id != (company.id if company else None)
                ):
                    old_pos = Position(
                        person_id=existing.id,  # type: ignore[arg-type]
                        company_id=existing.current_company_id,
                        title=existing.current_position_title,
                        is_current=False,
                    )
                    session.add(old_pos)

                existing.first_name = first_name or existing.first_name
                existing.last_name = last_name or existing.last_name
                existing.full_name = full_name or existing.full_name
                existing.email = email or existing.email
                existing.current_company_id = company.id if company else existing.current_company_id
                existing.current_position_title = position_title or existing.current_position_title
                if connected_date and (not existing.connected_date or connected_date > existing.connected_date):
                    existing.connected_date = connected_date
                existing.updated_at = datetime.utcnow()
                session.add(existing)
                result.merged += 1
            else:
                person = Person(
                    linkedin_url=linkedin_url,
                    full_name=full_name,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    current_company_id=company.id if company else None,
                    current_position_title=position_title,
                    connected_date=connected_date,
                    stage=Stage.not_contacted,
                    source=Source.csv_import,
                )
                session.add(person)
                session.flush()

                if position_title:
                    pos = Position(
                        person_id=person.id,  # type: ignore[arg-type]
                        company_id=company.id if company else None,
                        title=position_title,
                        is_current=True,
                    )
                    session.add(pos)

                result.imported += 1

        except Exception as exc:
            result.errors.append({"row": row_num, "error": str(exc)})
            result.skipped += 1
            continue

    session.commit()
    return result
