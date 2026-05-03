# AI CV Screener (Local LLM - Qwen 3.5)

## Overview

This project is an automated CV screening pipeline designed for **high-volume, low-stakes recruitment**.

It processes candidate resumes from ATS-generated emails and uses a **local LLM (Qwen 3.5)** to evaluate candidates.

---

## Key Features

- 📩 Email ingestion (via IMAP)
- 🔗 Auto-download CVs from ATS links (Moka)
- 📂 Batch processing of CV files
- 🤖 Local LLM screening (Qwen 3.5 via Ollama)
- 📊 Structured candidate evaluation
- 🚨 Telegram alerts for shortlisted candidates

---

## Why This Exists

Traditional ATS systems:
- Lack intelligent filtering
- Require manual CV review
- Are inefficient for high-volume hiring

This tool:
- Automates first-round screening
- Prioritizes speed over perfection
- Designed for roles like:
  - Admin
  - Customer Service
  - Junior HR
  - Low-risk hires

---

## Tech Stack

- Python
- PyMuPDF (PDF parsing)
- Ollama (Local LLM)
- Qwen 3.5
- IMAP (Email ingestion)
- Telegram Bot API

---

## Workflow

1. ATS sends candidate emails
2. Script reads inbox
3. Extracts download links
4. Downloads CVs
5. Runs LLM evaluation
6. Sends alerts for strong candidates

---

## Example Output

- Candidate Score
- Hire / No Hire / Interview
- Strengths / Weaknesses
- Matching analysis

---

## Philosophy

> Not trying to replace recruiters.  
> Trying to eliminate repetitive screening work.

---

## Future Improvements

- Ranking dashboard
- ATS integration
- Multi-role evaluation
- Auto interview scheduling

---

## Author

Tom Lee  
Talent Acquisition | HR Tech Builder
