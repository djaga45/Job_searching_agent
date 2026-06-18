import json
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from agent.config import DATA_DIR
from agent.models import UserProfile


def load_profile(path: Path | None = None) -> UserProfile:
    profile_path = path or DATA_DIR / "profile.json"
    with profile_path.open(encoding="utf-8") as f:
        return UserProfile.model_validate(json.load(f))


def load_resume_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        doc = Document(path)
        return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
    if suffix == ".pdf":
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported resume format: {suffix}")


def find_master_resume() -> Path | None:
    for name in ("master_resume.docx", "master_resume.pdf", "master_resume.txt", "master_resume.md"):
        candidate = DATA_DIR / name
        if candidate.exists():
            return candidate
    return None


def profile_to_text(profile: UserProfile) -> str:
    lines = [
        f"Name: {profile.name}",
        f"Email: {profile.email}",
        f"Phone: {profile.phone}",
        f"Location: {profile.location}",
        f"LinkedIn: {profile.linkedin}",
        f"GitHub: {getattr(profile, 'github', '')}",
        f"Target roles: {', '.join(profile.target_roles)}",
        f"Skills: {', '.join(profile.skills)}",
        f"Summary: {profile.summary}",
        "",
        "Experience:",
    ]
    for exp in profile.experience:
        lines.append(f"- {exp.title} at {exp.company} ({exp.dates})")
        for bullet in exp.bullets:
            lines.append(f"  * {bullet}")
    if profile.projects:
        lines.append("")
        lines.append("Projects:")
        for project in profile.projects:
            lines.append(f"- {project.title}: {project.description}")
            for bullet in project.bullets:
                lines.append(f"  * {bullet}")
    if profile.certifications:
        lines.append("")
        lines.append(f"Certifications: {', '.join(profile.certifications)}")
    if profile.awards:
        lines.append(f"Awards: {', '.join(profile.awards)}")
    if profile.education:
        lines.append("")
        lines.append("Education:")
        for edu in profile.education:
            lines.append(f"- {edu.degree}, {edu.institution} ({edu.dates})")
    return "\n".join(lines)