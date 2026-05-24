import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import requests
import dotenv
from datetime import datetime
import fitz  # PyMuPDF
import docx

# ============================================================
# ENVIRONMENT VARIABLES & PATH CONFIGURATION
# ============================================================
dotenv.load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_DIR = r"C:\Users\user\Desktop\CV_screener\Storage"
RAW_MARKDOWN_DIR = os.path.join(BASE_DIR, "raw_markdown")
DEALBREAKER_OUT_DIR = os.path.join(BASE_DIR, "dealbreakers")
EVALUATION_DIR = os.path.join(BASE_DIR, "evaluations")
PROCESSED_FILE = os.path.join(BASE_DIR, "processed_files.txt")

for directory in [RAW_MARKDOWN_DIR, DEALBREAKER_OUT_DIR, EVALUATION_DIR]:
    os.makedirs(directory, exist_ok=True)

TESTING_PROFILES_DIR = r"C:\Users\user\Desktop\CV_screener\Testing_profiles"
HIRING_BRIEF_FILE = r"C:\Users\user\Desktop\CV_screener\positions_criteria\Regional_HR_Lead.md"
DEALBREAKER_FILE = r"C:\Users\user\Desktop\CV_screener\positions_criteria\Dealbreaker.md"

TELEGRAM_REPORT_LIST = []

# ============================================================
# STATE MANAGEMENT (Processed files tracking)
# ============================================================
def load_processed():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def mark_processed(filename):
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(filename + "\n")

# ============================================================
# FILE READERS (PDF / DOCX / TXT)
# ============================================================
def read_pdf(path):
    try:
        doc = fitz.open(path)
        return "".join(page.get_text() for page in doc)
    except Exception as e:
        print(f"❌ PDF read failed: {e}")
        return ""

def read_docx(path):
    try:
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"❌ DOCX read failed: {e}")
        return ""

def read_cv(path):
    if path.lower().endswith(".pdf"):
        return read_pdf(path)
    if path.lower().endswith(".docx"):
        return read_docx(path)
    return ""

def read_text_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ============================================================
# LLM INTERFACE (Ollama, supports long context and extended timeout)
# ============================================================
def ask_llm(prompt):
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen3.6-32k",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_ctx": 16384,
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            },
            timeout=300
        )
        return res.json()["response"]
    except Exception as e:
        print(f"❌ LLM Request failed: {e}")
        return ""

# ============================================================
# PROMPT BUILDERS
# ============================================================
def build_dealbreaker_prompt(raw_cv, dealbreaker_criteria):
    current_date = datetime.now().strftime("%d %B %Y")
    return f"""
{dealbreaker_criteria}

today is {current_date}.

==================================================
RAW CV CONTENT TO EVALUATE:
==================================================
{raw_cv}

==================================================
OUTPUT (STRICTLY FOLLOW THE FORMAT REQ):
==================================================
Only read the english content in the CV and evaluate if any of the deal-breaker criteria are met.
"""

def build_evaluation_prompt(raw_cv, hiring_brief):
    current_date = datetime.now().strftime("%d %B %Y")
    return f"""
today is {current_date}.

You are an expert Talent Acquisition specialist. 
Evaluate this candidate based on the provided Hiring Brief. Determine their final tier into one of the four categories specified.

{hiring_brief}

==================================================
RAW CV CONTENT:
==================================================
{raw_cv}

==================================================
REQUIRED OUTPUT FORMAT:
==================================================
Provide a brief analysis based on the core pillars, and conclude with the precise recommendation header line (e.g., "## Strong Recommend", "## Recommend", "## Borderline", or "## Weak Fit").

Only read the english content in the CV and evaluate based on the hiring brief criteria.
"""

# ============================================================
# OUTPUT SAVING & HELPER FUNCTIONS
# ============================================================
def save_output(directory, filename, content, suffix=""):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(filename))[0]
    output_filename = f"{base_name}_{suffix}_{timestamp}.md" if suffix else f"{base_name}_{timestamp}.md"
    save_path = os.path.join(directory, output_filename)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 Saved: {save_path}")
    return save_path

def print_section(title, content, limit=2000):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    if len(content) > limit:
        print(content[:limit] + "\n... [TRUNCATED OUTPUT] ...")
    else:
        print(content)
    print("=" * 80)

def parse_recommendation(eval_text):
    eval_upper = eval_text.upper()
    if "STRONG RECOMMEND" in eval_upper:
        return "Strong Recommend ⭐"
    if "RECOMMEND" in eval_upper:
        return "Recommend ✅"
    if "BORDERLINE" in eval_upper:
        return "Borderline ⚠️"
    if "WEAK FIT" in eval_upper:
        return "Weak Fit ❌"
    return "Undetermined"

# ============================================================
# TELEGRAM NOTIFICATION
# ============================================================
def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠ Telegram not configured")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
        print("📲 Telegram summary sent successfully.")
    except Exception as e:
        print(f"❌ Telegram failed: {e}")

# ============================================================
# MAIN EXECUTION FLOW
# ============================================================
def run():
    processed = load_processed()

    if not os.path.exists(TESTING_PROFILES_DIR):
        print(f"❌ Testing folder path does not exist: {TESTING_PROFILES_DIR}")
        return

    local_files = [f for f in os.listdir(TESTING_PROFILES_DIR) if f.lower().endswith((".pdf", ".docx"))]
    print(f"📂 Found {len(local_files)} files in Testing_profiles directory.")

    if not local_files:
        print("📭 No candidate files found to process.")
        return

    hiring_brief = read_text_file(HIRING_BRIEF_FILE)
    dealbreaker_criteria = read_text_file(DEALBREAKER_FILE)

    for filename in local_files:
        if filename in processed:
            print(f"\n⏩ Already processed: {filename}")
            continue

        file_path = os.path.join(TESTING_PROFILES_DIR, filename)
        print(f"\n🧠 Processing: {filename}")

        # 1. Extract raw CV content
        raw_markdown = read_cv(file_path)
        if not raw_markdown.strip():
            print(f"⚠ Empty text extraction for CV: {filename}")
            continue

        print_section(f"RAW MARKDOWN: {filename}", raw_markdown)
        save_output(RAW_MARKDOWN_DIR, filename, raw_markdown, suffix="raw")

        # 2. Deal Breaker screening
        print("\n🛡 Running Stage 1: Deal-Breaker Screening...")
        dealbreaker_res = ask_llm(build_dealbreaker_prompt(raw_markdown, dealbreaker_criteria))
        print_section("DEAL BREAKER EVALUATION RESULT", dealbreaker_res)
        save_output(DEALBREAKER_OUT_DIR, filename, dealbreaker_res, suffix="dealbreaker")

        dealbreaker_upper = dealbreaker_res.upper()
        if any(flag in dealbreaker_upper for flag in ["RULED_OUT: YES", "RULED_OUT:YES", "FINAL RECOMMENDATION: REJECT"]):
            print(f"⛔ Candidate {filename} hit a Deal-Breaker. Ruling out.")
            save_output(EVALUATION_DIR, filename, f"# Deal Breaker Triggered\n\n{dealbreaker_res}", suffix="rejected")
            mark_processed(filename)
            continue

        # 3. Core capability evaluation (passed Deal Breaker)
        print("\n📋 Running Stage 2: Core Capability Evaluation...")
        evaluation = ask_llm(build_evaluation_prompt(raw_markdown[:15000], hiring_brief))
        if not evaluation.strip():
            print("❌ Stage 2 Core evaluation failed or empty response.")
            continue

        save_output(EVALUATION_DIR, filename, evaluation, suffix="evaluated")
        print_section("CORE EVALUATION REPORT", evaluation)

        rec_level = parse_recommendation(evaluation)
        TELEGRAM_REPORT_LIST.append((filename, rec_level))
        mark_processed(filename)
        print(f"✅ Completed entire workflow for: {filename}")

    # Send batch summary
    if TELEGRAM_REPORT_LIST:
        report = "📌 Screened Profiles Summary (Passed Deal-Breakers)\n\n"
        for i, (file, level) in enumerate(TELEGRAM_REPORT_LIST, 1):
            report += f"{i}. 📄 {file}\n   ↳ Status: {level}\n\n"
        print("\n" + report)
        send_telegram(report)
    else:
        print("\n📭 No candidates passed the deal-breaker criteria during this batch.")
        send_telegram("Batch Complete: 0 profiles passed the initial deal-breaker screening.")

if __name__ == "__main__":
    run()
