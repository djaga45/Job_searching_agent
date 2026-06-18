import json
import sqlite3
from datetime import datetime, timezone

from agent.config import DB_PATH
from agent.models import ApplicationDraft, JobPosting, ScoredJob, TailoredResume


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                description TEXT,
                url TEXT,
                source TEXT,
                salary TEXT,
                remote INTEGER DEFAULT 0,
                posted_at TEXT,
                fit_score INTEGER,
                fit_reason TEXT,
                matched_skills TEXT,
                missing_skills TEXT,
                status TEXT DEFAULT 'discovered',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS applications (
                job_id TEXT PRIMARY KEY,
                cover_letter TEXT,
                why_this_role TEXT,
                suggested_answers TEXT,
                tailored_resume_path TEXT,
                approved INTEGER DEFAULT 0,
                applied INTEGER DEFAULT 0,
                applied_at TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            );
            """
        )


def upsert_job(scored: ScoredJob) -> None:
    now = datetime.now(timezone.utc).isoformat()
    job = scored.job
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs (
                id, title, company, location, description, url, source,
                salary, remote, posted_at, fit_score, fit_reason,
                matched_skills, missing_skills, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered', ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                fit_score=excluded.fit_score,
                fit_reason=excluded.fit_reason,
                matched_skills=excluded.matched_skills,
                missing_skills=excluded.missing_skills,
                updated_at=excluded.updated_at
            """,
            (
                job.id,
                job.title,
                job.company,
                job.location,
                job.description,
                job.url,
                job.source,
                job.salary,
                int(job.remote),
                job.posted_at,
                scored.fit_score,
                scored.fit_reason,
                json.dumps(scored.matched_skills),
                json.dumps(scored.missing_skills),
                now,
                now,
            ),
        )


def list_jobs(status: str | None = None, min_score: int = 0) -> list[dict]:
    query = "SELECT * FROM jobs WHERE fit_score >= ?"
    params: list[object] = [min_score]
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY fit_score DESC, created_at DESC"
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_job(job_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def update_job_status(job_id: str, status: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, job_id),
        )


def save_application(
    job_id: str,
    draft: ApplicationDraft,
    tailored_path: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO applications (
                job_id, cover_letter, why_this_role, suggested_answers,
                tailored_resume_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                cover_letter=excluded.cover_letter,
                why_this_role=excluded.why_this_role,
                suggested_answers=excluded.suggested_answers,
                tailored_resume_path=excluded.tailored_resume_path,
                updated_at=excluded.updated_at
            """,
            (
                job_id,
                draft.cover_letter,
                draft.why_this_role,
                json.dumps(draft.suggested_answers),
                tailored_path,
                now,
                now,
            ),
        )
        conn.execute(
            "UPDATE jobs SET status = 'prepared', updated_at = ? WHERE id = ?",
            (now, job_id),
        )


def get_application(job_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    return dict(row) if row else None


def approve_application(job_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "UPDATE applications SET approved = 1, updated_at = ? WHERE job_id = ?",
            (now, job_id),
        )
        conn.execute(
            "UPDATE jobs SET status = 'approved', updated_at = ? WHERE id = ?",
            (now, job_id),
        )


def mark_applied(job_id: str, notes: str = "") -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE applications
            SET applied = 1, applied_at = ?, notes = ?, updated_at = ?
            WHERE job_id = ?
            """,
            (now, notes, now, job_id),
        )
        conn.execute(
            "UPDATE jobs SET status = 'applied', updated_at = ? WHERE id = ?",
            (now, job_id),
        )


def job_from_row(row: dict) -> JobPosting:
    return JobPosting(
        id=row["id"],
        title=row["title"],
        company=row["company"],
        location=row["location"] or "",
        description=row["description"] or "",
        url=row["url"] or "",
        source=row["source"] or "",
        salary=row["salary"] or "",
        remote=bool(row["remote"]),
        posted_at=row["posted_at"] or "",
    )