from agent.application_drafter import draft_application
from agent.config import settings
from agent.job_scorer import score_jobs
from agent.job_search import search_jobs
from agent.models import UserProfile
from agent.resume_tailor import tailor_resume
from agent.storage import init_db, save_application, upsert_job


def run_job_search(profile: UserProfile, use_llm_scoring: bool = True) -> list[dict]:
    init_db()
    jobs = search_jobs(profile)
    scored = score_jobs(jobs, profile, use_llm=use_llm_scoring)
    for item in scored:
        upsert_job(item)
    return [
        {
            "id": item.job.id,
            "title": item.job.title,
            "company": item.job.company,
            "fit_score": item.fit_score,
            "url": item.job.url,
            "source": item.job.source,
        }
        for item in scored
    ]


def prepare_application(profile: UserProfile, job_id: str) -> dict:
    from agent.storage import get_job, job_from_row

    row = get_job(job_id)
    if not row:
        raise ValueError(f"Job not found: {job_id}")

    job = job_from_row(row)
    tailored, resume_path = tailor_resume(profile, job)
    draft = draft_application(profile, job)
    save_application(job_id, draft, str(resume_path))

    return {
        "job_id": job_id,
        "resume_path": str(resume_path),
        "changes_made": tailored.changes_made,
        "cover_letter": draft.cover_letter,
        "why_this_role": draft.why_this_role,
        "suggested_answers": draft.suggested_answers,
        "apply_url": job.url,
        "min_fit_score": settings.min_fit_score,
    }