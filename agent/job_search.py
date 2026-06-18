import hashlib
import re
from html import unescape

import requests

from agent.config import settings
from agent.models import JobPosting, UserProfile

REQUEST_TIMEOUT = 20
HEADERS = {"User-Agent": "JobHuntAgent/1.0 (personal job search assistant)"}


def _make_id(source: str, url: str, title: str, company: str) -> str:
    raw = f"{source}|{url}|{title}|{company}".lower()
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _clean_html(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_india_job(job: JobPosting, profile: UserProfile) -> bool:
    if not profile.country_filter or profile.country_filter.lower() != "india":
        return True
    if job.source.lower() == "adzuna":
        return True
    location_blob = f"{job.location} {job.description} {job.title}".lower()
    india_terms = profile.india_locations or ["india"]
    remote_india_terms = ["asia", "worldwide", "world", "anywhere", "global", "emea", "apac"]
    if any(term in location_blob for term in india_terms):
        return True
    if job.remote and any(term in location_blob for term in remote_india_terms):
        return True
    return False


def _term_in_text(term: str, text: str) -> bool:
    if len(term) <= 3:
        return re.search(rf"\b{re.escape(term)}\b", text) is not None
    return term in text


def _is_genai_job(job: JobPosting, profile: UserProfile) -> bool:
    title = job.title.lower()
    blob = f"{job.title} {job.description}".lower()
    genai_terms = profile.required_keywords or [
        "generative ai",
        "gen ai",
        "genai",
        "llm",
        "large language model",
        "langchain",
        "rag",
    ]
    title_hit = any(_term_in_text(term, title) for term in genai_terms)
    if title_hit:
        return True

    ai_role_titles = ["ai engineer", "ai developer", "ai architect", "llm engineer", "ml engineer"]
    if any(role in title for role in ai_role_titles):
        desc_signals = [
            "generative ai",
            "gen ai",
            "genai",
            "llm",
            "large language model",
            "langchain",
            "rag",
            "retrieval",
            "agent",
            "prompt",
            "gpt",
            "transformer",
        ]
        if any(_term_in_text(term, blob) for term in desc_signals):
            return True

    strong_terms = [
        "generative ai",
        "gen ai",
        "genai",
        "large language model",
        "langchain",
        "retrieval augmented",
        "prompt engineer",
    ]
    return sum(1 for term in strong_terms if _term_in_text(term, blob)) >= 1


def _matches_profile(job: JobPosting, profile: UserProfile) -> bool:
    blob = f"{job.title} {job.description} {job.company}".lower()
    for keyword in profile.exclude_keywords:
        if keyword.lower() in blob:
            return False

    if not _is_genai_job(job, profile):
        return False

    if not _is_india_job(job, profile):
        return False

    title_blob = job.title.lower()
    role_hit = any(role.lower() in title_blob for role in profile.target_roles)
    if not role_hit:
        genai_skill_hits = sum(
            1
            for skill in profile.skills
            if skill.lower() in blob
            and skill.lower() in {"generative ai", "langchain", "langgraph", "rag", "ollama", "large language models"}
        )
        if genai_skill_hits < 1 and "ai" not in title_blob:
            return False
    return True


def search_remoteok(profile: UserProfile, limit: int = 20) -> list[JobPosting]:
    response = requests.get(
        "https://remoteok.com/api",
        headers={**HEADERS, "Accept": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    jobs: list[JobPosting] = []

    for item in payload:
        if not isinstance(item, dict) or "position" not in item:
            continue
        title = item.get("position", "").strip()
        if not title:
            continue
        description = _clean_html(item.get("description", ""))
        company = item.get("company", "Unknown").strip()
        location = item.get("location", "Remote").strip() or "Remote"
        url = item.get("url") or item.get("apply_url") or ""
        if url and not url.startswith("http"):
            url = f"https://remoteok.com{url}"

        job = JobPosting(
            id=_make_id("remoteok", url, title, company),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            source="RemoteOK",
            salary=item.get("salary", "") or "",
            remote=True,
            posted_at=str(item.get("date", "")),
        )
        if _matches_profile(job, profile):
            jobs.append(job)
        if len(jobs) >= limit:
            break
    return jobs


def search_arbeitnow(profile: UserProfile, limit: int = 20) -> list[JobPosting]:
    response = requests.get(
        "https://www.arbeitnow.com/api/job-board-api",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    jobs: list[JobPosting] = []

    for item in payload.get("data", []):
        title = item.get("title", "").strip()
        if not title:
            continue
        tags = " ".join(item.get("tags", []))
        description = _clean_html(item.get("description", ""))
        company = item.get("company_name", "Unknown").strip()
        url = item.get("url", "")
        location = item.get("location", "") or "Remote"
        remote = bool(item.get("remote", False)) or "remote" in location.lower()

        job = JobPosting(
            id=_make_id("arbeitnow", url, title, company),
            title=title,
            company=company,
            location=location,
            description=f"{tags}\n\n{description}".strip(),
            url=url,
            source="Arbeitnow",
            salary="",
            remote=remote,
            posted_at=str(item.get("created_at", "")),
        )
        if _matches_profile(job, profile):
            jobs.append(job)
        if len(jobs) >= limit:
            break
    return jobs


def search_adzuna(profile: UserProfile, limit: int = 20) -> list[JobPosting]:
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        return []

    query = "generative ai engineer"
    url = (
        f"https://api.adzuna.com/v1/api/jobs/{settings.adzuna_country}/search/1"
        f"?app_id={settings.adzuna_app_id}&app_key={settings.adzuna_app_key}"
        f"&results_per_page={limit}&what={requests.utils.quote(query)}"
    )
    if profile.location:
        url += f"&where={requests.utils.quote(profile.location)}"

    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    jobs: list[JobPosting] = []

    for item in payload.get("results", []):
        title = item.get("title", "").strip()
        if not title:
            continue
        company = (item.get("company") or {}).get("display_name", "Unknown")
        description = _clean_html(item.get("description", ""))
        location = (item.get("location") or {}).get("display_name", profile.location)
        url = item.get("redirect_url", "")
        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")
        salary = ""
        if salary_min and salary_max:
            salary = f"£{int(salary_min):,} - £{int(salary_max):,}"

        job = JobPosting(
            id=_make_id("adzuna", url, title, company),
            title=title,
            company=company,
            location=location or "",
            description=description,
            url=url,
            source="Adzuna",
            salary=salary,
            remote="remote" in f"{title} {description} {location}".lower(),
            posted_at=str(item.get("created", "")),
        )
        if _matches_profile(job, profile):
            jobs.append(job)
    return jobs


def search_remotive(profile: UserProfile, limit: int = 20) -> list[JobPosting]:
    response = requests.get(
        "https://remotive.com/api/remote-jobs",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    jobs: list[JobPosting] = []

    for item in response.json().get("jobs", []):
        title = (item.get("title") or item.get("job_title") or "").strip()
        if not title:
            continue
        description = _clean_html(item.get("description", ""))
        company = (item.get("company_name") or "Unknown").strip()
        location = item.get("candidate_required_location", "") or "Remote"
        url = item.get("url", "")
        job = JobPosting(
            id=_make_id("remotive", url, title, company),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            source="Remotive",
            salary=item.get("salary", "") or "",
            remote=True,
            posted_at=str(item.get("publication_date", "")),
        )
        if _matches_profile(job, profile):
            jobs.append(job)
        if len(jobs) >= limit:
            break
    return jobs


def search_jobs(profile: UserProfile, max_results: int | None = None) -> list[JobPosting]:
    limit = max_results or settings.max_jobs_per_search
    per_source = max(5, limit // 3)

    collectors = [
        search_adzuna(profile, per_source),
        search_remotive(profile, per_source),
        search_remoteok(profile, per_source),
        search_arbeitnow(profile, per_source),
    ]

    seen: set[str] = set()
    merged: list[JobPosting] = []
    for batch in collectors:
        for job in batch:
            if job.id in seen:
                continue
            seen.add(job.id)
            merged.append(job)
            if len(merged) >= limit:
                return merged
    return merged