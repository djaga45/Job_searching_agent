from agent.llm import invoke_json
from agent.models import ApplicationDraft, JobPosting, UserProfile
from agent.profile_loader import profile_to_text


def draft_application(profile: UserProfile, job: JobPosting) -> ApplicationDraft:
    system = (
        "You draft job application materials. Be professional, specific, and truthful. "
        "Do not claim experience the candidate does not have. Return strict JSON with "
        "keys: cover_letter (string), why_this_role (string), suggested_answers "
        "(object mapping common form questions to answers)."
    )
    user = (
        f"CANDIDATE:\n{profile_to_text(profile)}\n\n"
        f"JOB:\nTitle: {job.title}\nCompany: {job.company}\n"
        f"Location: {job.location}\nURL: {job.url}\n"
        f"Description:\n{job.description[:4000]}\n\n"
        "Write a concise cover letter (max 250 words), a short 'why this role' "
        "paragraph, and answers for: years_of_experience, salary_expectation, "
        "right_to_work, notice_period."
    )

    result = invoke_json(system, user)
    return ApplicationDraft(
        job_id=job.id,
        cover_letter=str(result["cover_letter"]),
        why_this_role=str(result["why_this_role"]),
        suggested_answers={
            str(k): str(v) for k, v in dict(result.get("suggested_answers", {})).items()
        },
    )