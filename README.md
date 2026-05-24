# AI-Powered CV Screener (Powered by Local LLM, Qwen 3.6)

This project is an automated CV screening and evaluation pipeline powered by a local Large Language Model (LLM). It utilizes a **Two-Stage Screening Mechanism** to filter out unqualified candidates early and deliver structured evaluation reports via Telegram.

---

## 📌 How It Works

1. **Stage 1: Deal-Breaker Screening** – Evaluates the CV against strict knockout criteria. If a candidate triggers a deal-breaker, the system logs a `RULED_OUT: YES` status and immediately stops processing to save computing resources.
2. **Stage 2: Core Evaluation** – Candidates who pass Stage 1 undergo a comprehensive assessment against the target job brief and are categorized into recommendation tiers (`Strong Recommend`, `Recommend`, `Borderline`, or `Weak Fit`).
3. **Stage 3: Telegram Notification** – Summarizes the batch results and dispatches a clean report directly to your configured Telegram channel.

---

## 📂 Folder Setup

Before running the script, ensure your workspace is structured as follows:

```text
CV_screener/
│
├── positions_criteria/             # Put your criteria files here
│   ├── Regional_HR_Lead.md         # Target job requirements
│   └── Dealbreaker.md              # Knockout rules
│
├── Testing_profiles/               # Drop incoming CVs here (.pdf, .docx)
│
└── Storage/                        # System-managed outputs (Auto-generated)
    ├── processed_files.txt         # State tracker to prevent duplicate processing
    ├── raw_markdown/               # Raw text extractions
    ├── dealbreakers/               # Stage 1 reports
    └── evaluations/                # Stage 2 reports and rejection logs

```

---

## 🛠 Setup & Requirements

### 1. Dependencies

Install the required libraries:

```bash
pip install pymupdf python-docx python-dotenv requests

```

### 2. Local LLM (Ollama)

The script interfaces with a local Ollama instance to keep data completely private.

* **Model:** Optimized for `qwen3.6-32k` (or your preferred local model).
* **Endpoint:** `http://localhost:11434/api/generate`
* **Context:** Configured with a `16,384` context window and a low temperature (`0.1`) for strict formatting compliance.

### 3. Environment Variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN="your_bot_token_here"
TELEGRAM_CHAT_ID="your_chat_id_here"

```

---

## 🚀 Usage

1. Drop your markdown criteria into `positions_criteria/`.
2. Add candidate CV files to `Testing_profiles/`.
3. Run the script:
```bash
python "Gemini version_Qwen3.6.py"

```


4. Check your generated reports in the `Storage/` folders or check your Telegram notifications.
