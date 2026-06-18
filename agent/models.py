from typing import Literal

from pydantic import BaseModel, Field


class Experience(BaseModel):
    title: str
    company: str
    dates: str
    bullets: list[str]


class Education(BaseModel):
    degree: str
    institution: str
    dates: str


class Project(BaseModel):
    title: str
    description: str = ""
    bullets: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    name: str
    email: str
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    location: str = ""
    target_roles: list[str]
    required_keywords: list[str] = Field(default_factory=list)
    country_filter: str = ""
    india_locations: list[str] = Field(default_factory=list)
    skills: list[str]
    min_salary_gbp: int | None = None
    remote_preference: Literal["remote", "hybrid", "onsite", "remote_or_hybrid"] = "remote_or_hybrid"
    exclude_keywords: list[str] = Field(default_factory=list)
    summary: str
    experience: list[Experience]
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)


class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    salary: str = ""
    remote: bool = False
    posted_at: str = ""


class ScoredJob(BaseModel):
    job: JobPosting
    fit_score: int
    fit_reason: str
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class TailoredResume(BaseModel):
    job_id: str
    summary: str
    experience: list[Experience]
    skills_highlight: list[str]
    changes_made: list[str]


class ApplicationDraft(BaseModel):
    job_id: str
    cover_letter: str
    why_this_role: str
    suggested_answers: dict[str, str] = Field(default_factory=dict)