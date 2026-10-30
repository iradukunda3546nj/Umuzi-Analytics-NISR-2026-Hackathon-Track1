# Deployment Guide (Streamlit Community Cloud)

**Status on 2026-10-29: not deployed.** No public URL exists. Deployment needs the team's GitHub and Streamlit accounts and explicit authorisation.

## Steps
1. Create a **public** GitHub repository (for example `umuzi-analytics`).
2. From the project folder:
   ```bash
   git init
   git add .
   git status            # confirm submission_private/, data/incoming/, data/quarantine/ are NOT listed
   git commit -m "Umuzi Analytics: NISR 2026 Hackathon, Track 1"
   git branch -M main
   git remote add origin https://github.com/<account>/umuzi-analytics.git
   git push -u origin main
   ```
3. Sign in at https://share.streamlit.io with GitHub, choose **Create app**, pick the repository, branch `main`, main file `app.py`. Under Advanced settings choose Python 3.12 or 3.13.
4. Deploy, then open the URL in a **private browser window** and check every view ([W] p.15).
5. Paste the URL into `README.md` and the submission form.
6. Open the link shortly before the deadline so the app is awake when judges check ([W] p.15). The free tier sleeps after 12 hours without visitors ([W] p.4).

## What the deployed app needs
- `app.py`, `requirements.txt`, `.streamlit/config.toml`, `src/`, `data/snapshots/`, `data/raw/boundaries/`, `data/reference/`. All are in the repository.
- No secrets, no database, no network calls at run time.

## Verified locally
- `streamlit run app.py` starts and serves all views (Python 3.14, Streamlit 1.66.1).
- `pytest`: 38 passed.
- Not verified: installation on Streamlit Cloud's Python version. `requirements.txt` uses lower bounds so the cloud can choose compatible wheels.
