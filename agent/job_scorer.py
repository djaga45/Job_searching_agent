from agent.config import settings
from agent.job_search import _is_genai_job
from agent.llm import invoke_json
from agent.models import JobPosting, ScoredJob, UserProfile
from agent.profile_loader import profile_to_text


def _keyword_score(job: JobPosting, profile: UserProfile) -> tuple[int, list[str], list[str]]:
    blob = f"{job.title} {job.description}".lower()
    matched = [skill for skill in profile.skills if skill.lower() in blob]
    missing = [skill for skill in profile.skills if skill.lower() not in blob][:8]

    title_lower = job.title.lower()
    title_bonus = 0
    for role in profile.target_roles:
        role_lower = role.lower()
        if role_lower in title_lower:
            title_bonus = 30
            break
        role_tokens = [token for token in role_lower.split() if len(token) > 3]
        if role_tokens and sum(1 for token in role_tokens if token in title_lower) >= 2:
            title_bonus = 20
            break

    remote_bonus = 10 if job.remote and profile.remote_preference != "onsite" else 0
    genai_bonus = 20 if _is_genai_job(job, profile) else 0
    score = min(100, title_bonus + remote_bonus + genai_bonus + len(matched) * 8 + 5)
    return score, matched, missing


def score_job(job: JobPosting, profile: UserProfile, use_llm: bool = True) -> ScoredJob:
    base_score, matched, missing = _keyword_score(job, profile)

    if not use_llm or not settings.groq_api_key:
        reason = "Keyword-based match using your target roles and skills."
        if matched:
            reason += f" Matched: {', '.join(matched[:6])}."
        return ScoredJob(
            job=job,
            fit_score=base_score,
            fit_reason=reason,
            matched_skills=matched,
            missing_skills=missing,
        )

    system = (
        "You score job fit for a candidate. Return strict JSON only with keys: "
        "fit_score (0-100 integer), fit_reason (string), matched_skills (array), "
        "missing_skills (array). Be realistic. Never inflate scores."
    )
    user = (
        f"CANDIDATE PROFILE:\n{profile_to_text(profile)}\n\n"
        f"JOB:\nTitle: {job.title}\nCompany: {job.company}\n"
        f"Location: {job.location}\nSalary: {job.salary}\n"
        f"Description:\n{job.description[:3500]}"
    )

    try:
        result = invoke_json(system, user)
        return ScoredJob(
            job=job,
            fit_score=int(result.get("fit_score", base_score)),
            fit_reason=str(result.get("fit_reason", "")),
            matched_skills=list(result.get("matched_skills", matched)),
            missing_skills=list(result.get("missing_skills", missing)),
        )
    except Exception:
        return ScoredJob(
            job=job,
            fit_score=base_score,
            fit_reason="LLM scoring unavailable; used keyword match instead.",
            matched_skills=matched,
            missing_skills=missing,
        )


def score_jobs(
    jobs: list[JobPosting],
    profile: UserProfile,
    min_score: int | None = None,
    use_llm: bool = True,
) -> list[ScoredJob]:
    threshold = min_score if min_score is not None else settings.min_fit_score
    scored = [score_job(job, profile, use_llm=use_llm) for job in jobs]
    return [item for item in scored if item.fit_score >= threshold]