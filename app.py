import json
from pathlib import Path

import streamlit as st

from agent.config import DATA_DIR, settings
from agent.orchestrator import prepare_application, run_job_search
from agent.profile_loader import load_profile
from agent.storage import (
    approve_application,
    get_application,
    get_job,
    init_db,
    list_jobs,
    mark_applied,
    update_job_status,
)

st.set_page_config(page_title="Job Hunt Agent", layout="wide")
st.title("Job Hunt Agent")
st.caption("Search jobs, tailor your resume, draft applications — you approve before applying.")

init_db()

try:
    profile = load_profile()
except Exception as exc:
    st.error(f"Could not load profile.json: {exc}")
    st.stop()

if not settings.groq_api_key:
    st.warning(
        "Add `GROQ_API_KEY` to `.env` for resume tailoring and application drafts. "
        "Job search still works without it."
    )

with st.sidebar:
    st.header("Your targets")
    st.write(", ".join(profile.target_roles))
    st.write(f"Skills: {', '.join(profile.skills[:8])}{'...' if len(profile.skills) > 8 else ''}")
    st.write(f"Min fit score: {settings.min_fit_score}")
    st.write("Filter: **Generative AI only · India**")
    if not settings.adzuna_app_id:
        st.warning(
            "For **India on-site/hybrid** Gen AI jobs, add free Adzuna API keys to `.env` "
            "(get them at developer.adzuna.com)."
        )
    st.markdown("Edit `data/profile.json` to change roles or keywords.")

tab_search, tab_queue, tab_prepare = st.tabs(["Search", "Job queue", "Prepare & apply"])

with tab_search:
    col1, col2 = st.columns([1, 3])
    with col1:
        use_llm = st.checkbox("Use AI scoring", value=bool(settings.groq_api_key))
        if st.button("Run job search", type="primary", use_container_width=True):
            with st.spinner("Searching Adzuna, Remotive, RemoteOK, and Arbeitnow..."):
                try:
                    results = run_job_search(profile, use_llm_scoring=use_llm)
                    st.session_state["last_search_count"] = len(results)
                except Exception as exc:
                    st.error(f"Search failed: {exc}")
    with col2:
        count = st.session_state.get("last_search_count")
        if count is not None:
            st.success(f"Saved {count} matching jobs to your queue.")

with tab_queue:
    status_filter = st.selectbox(
        "Status",
        ["all", "discovered", "prepared", "approved", "applied", "skipped"],
        index=0,
    )
    min_score = st.slider("Minimum fit score", 0, 100, settings.min_fit_score)
    jobs = list_jobs(None if status_filter == "all" else status_filter, min_score)

    if not jobs:
        st.info("No jobs yet. Run a search first.")
    else:
        for row in jobs:
            with st.expander(
                f"[{row['fit_score']}] {row['title']} @ {row['company']} ({row['status']})",
                expanded=False,
            ):
                st.markdown(f"**Source:** {row['source']}")
                st.markdown(f"**Location:** {row['location'] or 'N/A'}")
                if row.get("salary"):
                    st.markdown(f"**Salary:** {row['salary']}")
                st.markdown(f"**Why it fits:** {row['fit_reason']}")
                if row.get("matched_skills"):
                    st.markdown(f"**Matched skills:** {row['matched_skills']}")
                if row.get("missing_skills"):
                    st.markdown(f"**Gaps:** {row['missing_skills']}")
                st.markdown(f"[View job]({row['url']})")
                st.text(row["description"][:1200] + ("..." if len(row["description"] or "") > 1200 else ""))

                action_cols = st.columns(4)
                if action_cols[0].button("Prepare", key=f"prep_{row['id']}"):
                    st.session_state["selected_job_id"] = row["id"]
                    st.session_state["go_prepare"] = True
                    st.rerun()
                if action_cols[1].button("Skip", key=f"skip_{row['id']}"):
                    update_job_status(row["id"], "skipped")
                    st.rerun()

with tab_prepare:
    job_options = {f"{row['title']} @ {row['company']}": row["id"] for row in list_jobs()}
    selected_label = st.selectbox("Select job", list(job_options.keys()) if job_options else [])
    selected_job_id = job_options.get(selected_label)

    if st.session_state.get("go_prepare") and st.session_state.get("selected_job_id"):
        selected_job_id = st.session_state["selected_job_id"]
        st.session_state["go_prepare"] = False

    if not selected_job_id:
        st.info("Pick a job from the queue to prepare an application.")
    else:
        job_row = get_job(selected_job_id)
        app_row = get_application(selected_job_id)

        st.subheader(f"{job_row['title']} at {job_row['company']}")
        st.link_button("Open job posting", job_row["url"])

        if st.button("Generate tailored resume + application draft", type="primary"):
            if not settings.groq_api_key:
                st.error("GROQ_API_KEY is required for resume tailoring.")
            else:
                with st.spinner("Tailoring resume and drafting application..."):
                    try:
                        result = prepare_application(profile, selected_job_id)
                        st.session_state["last_prepare"] = result
                    except Exception as exc:
                        st.error(f"Preparation failed: {exc}")

        result = st.session_state.get("last_prepare") or (
            {
                "resume_path": app_row.get("tailored_resume_path") if app_row else None,
                "cover_letter": app_row.get("cover_letter") if app_row else "",
                "why_this_role": app_row.get("why_this_role") if app_row else "",
                "suggested_answers": json.loads(app_row.get("suggested_answers") or "{}")
                if app_row
                else {},
                "apply_url": job_row["url"],
            }
            if app_row
            else None
        )

        if result:
            if result.get("resume_path") and Path(result["resume_path"]).exists():
                with open(result["resume_path"], "rb") as f:
                    st.download_button(
                        "Download tailored resume",
                        data=f,
                        file_name=Path(result["resume_path"]).name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )

            st.markdown("### Cover letter")
            st.text_area("Cover letter", result.get("cover_letter", ""), height=220)

            st.markdown("### Why this role")
            st.text_area("Why this role", result.get("why_this_role", ""), height=120)

            if result.get("suggested_answers"):
                st.markdown("### Suggested form answers")
                st.json(result["suggested_answers"])

            approve_col, applied_col = st.columns(2)
            if approve_col.button("Approve application", type="primary"):
                approve_application(selected_job_id)
                st.success("Approved. Open the job link and submit manually with the tailored files.")
            if applied_col.button("Mark as applied"):
                mark_applied(selected_job_id, notes="Submitted by user")
                st.success("Marked as applied.")

            st.info(
                "Auto-submit is intentionally disabled. Review everything, then apply on the "
                "company site using your tailored resume and drafted answers."
            )