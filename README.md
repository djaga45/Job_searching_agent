# Job Hunt Agent

An AI-powered job hunting assistant that searches for **Generative AI roles in India**, scores job fit, tailors your resume per role, and drafts cover letters — with **human approval** before you apply.

Built with **Python**, **Streamlit**, **LangChain**, and **Groq**.

---

## Features

- **Job search** from Adzuna (India), Remotive, RemoteOK, and Arbeitnow
- **Gen AI filter** — only roles matching LLM / RAG / LangChain / Generative AI keywords
- **India filter** — India locations + remote roles open to Asia / Worldwide
- **Fit scoring** — keyword-based or AI-powered (Groq)
- **Resume tailoring** — generates a `.docx` per job (no fake experience)
- **Application drafts** — cover letter + suggested form answers
- **Approval workflow** — you review before applying (auto-submit disabled by design)

---

## Project structure

```
job-hunt-agent/
├── app.py                      # Streamlit dashboard
├── run_app.bat                 # Windows quick-start script
├── agent/
│   ├── job_search.py           # Fetches jobs from APIs
│   ├── job_scorer.py           # Scores job fit
│   ├── resume_tailor.py        # Tailors resume per job
│   ├── application_drafter.py  # Drafts cover letter
│   ├── orchestrator.py         # Main workflow
│   ├── storage.py              # SQLite job tracking
│   └── config.py               # Settings
├── data/
│   ├── profile.example.json    # Template — copy to profile.json
│   └── master_resume.example.txt
├── output/                     # Generated resumes (created at runtime)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Prerequisites

- **Python 3.11+** (3.14 works)
- **Groq API key** — [console.groq.com](https://console.groq.com)
- **Adzuna API keys** (optional, recommended for India on-site jobs) — [developer.adzuna.com](https://developer.adzuna.com)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/job-hunt-agent.git
cd job-hunt-agent
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
```

Edit `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3-32b

# Optional — more India job listings
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=in
```

### 4. Add your profile and resume

```bash
copy data\profile.example.json data\profile.json        # Windows
# cp data/profile.example.json data/profile.json          # macOS / Linux
```

Edit `data/profile.json` with your real details (name, email, skills, experience).

Add your resume to `data/` as one of:

- `master_resume.pdf` (recommended)
- `master_resume.docx`
- `master_resume.txt`

---

## Run the app

**Windows — double-click:**

```
run_app.bat
```

**Or from terminal:**

```powershell
# Windows
.\venv\Scripts\streamlit.exe run app.py

# macOS / Linux
streamlit run app.py
```

Open your browser at **http://localhost:8501** (or `:8502` if 8501 is in use).

---

## How to use

1. **Search** tab → click **Run job search**
2. **Job queue** tab → review matches → click **Prepare** on good roles
3. **Prepare & apply** tab → generate tailored resume + cover letter
4. **Approve** → download files → apply manually on the company site
5. **Mark as applied** when done

---

## Configuration

| File | Purpose |
|------|---------|
| `data/profile.json` | Your skills, target roles, experience, filters |
| `.env` | API keys and model settings |
| `agent/config.py` | `min_fit_score`, `max_jobs_per_search` defaults |

### Gen AI + India filters

Set in `data/profile.json`:

- `target_roles` — job titles to target
- `required_keywords` — Gen AI terms (llm, rag, langchain, etc.)
- `country_filter` — `"india"`
- `india_locations` — cities and remote regions (asia, worldwide, apac)

---

## GitHub hosting

### Before you push — important

**Never commit these files** (they are in `.gitignore`):

| File | Why |
|------|-----|
| `.env` | Contains API keys |
| `data/profile.json` | Your personal email, phone, experience |
| `data/master_resume.*` | Your private resume |
| `jobs.db` | Your job search history |
| `venv/` | Virtual environment (too large) |
| `output/` | Generated tailored resumes |

### Push to GitHub

```bash
cd job-hunt-agent
git init
git add .
git status          # verify .env and profile.json are NOT listed
git commit -m "Initial commit: Job Hunt Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/job-hunt-agent.git
git push -u origin main
```

### Create the repo on GitHub first

1. Go to [github.com/new](https://github.com/new)
2. Name it `job-hunt-agent`
3. Do **not** add a README (you already have one)
4. Copy the remote URL and use the commands above

---

## API keys

| Service | Required | Get keys |
|---------|----------|----------|
| Groq | Yes (for resume tailoring) | [console.groq.com](https://console.groq.com) |
| Adzuna | No (recommended for India jobs) | [developer.adzuna.com](https://developer.adzuna.com) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GROQ_API_KEY is missing` | Create `.env` from `.env.example` and add your key |
| No jobs found | Add Adzuna keys for India listings; lower `min_fit_score` in `agent/config.py` |
| `python` not found (Windows) | Use `py` instead: `py -m venv venv` |
| Port already in use | Streamlit will use 8502 automatically, or run `streamlit run app.py --server.port 8503` |

---

## Tech stack

- [Streamlit](https://streamlit.io) — UI
- [LangChain](https://langchain.com) + [Groq](https://groq.com) — LLM orchestration
- [ChromaDB](https://www.trychroma.com) — not used here; SQLite for job tracking
- [python-docx](https://python-docx.readthedocs.io) — resume generation
- [pypdf](https://pypdf.readthedocs.io) — resume parsing

---

## Roadmap

- [ ] LinkedIn / Naukri integration
- [ ] Scheduled daily job search
- [ ] Email alerts for new matches
- [ ] Browser-assisted apply (Playwright, human-in-the-loop)

---

## License

MIT — use freely for personal job hunting.

---

## Author

Built for automated Generative AI job search with resume tailoring and application drafting.