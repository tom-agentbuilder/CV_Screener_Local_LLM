import sys
sys.stdout.reconfigure(encoding='utf-8')

import imaplib
import email
import re
import os
import requests
import zipfile
import fitz
import html
from email.header import decode_header

# ========= CONFIG =========
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "your_email@gmail.com"
APP_PASSWORD = "your_app_password"

DOWNLOAD_DIR = r"C:\Users\user\Downloads"
SKILLS_PATH = r"C:\Users\user\Desktop\CV_screener\skills.md.txt"

TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

# ========= EMAIL =========

def decode_mime_words(s):
    if not s:
        return ""
    decoded = decode_header(s)
    out = ""
    for text, enc in decoded:
        if isinstance(text, bytes):
            try:
                out += text.decode(enc or "utf-8", errors="ignore")
            except:
                out += text.decode("utf-8", errors="ignore")
        else:
            out += text
    return out

def extract_links(msg):
    links = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                body = part.get_payload(decode=True).decode(errors="ignore")
                body = html.unescape(body)
                links += re.findall(r'https?://[^\s"<>]+', body)
    return list(set([l for l in links if ".zip" in l]))

def download_zip(url):
    filename = url.split("/")[-1].split("?")[0]
    path = os.path.join(DOWNLOAD_DIR, filename)

    r = requests.get(url)
    r.raise_for_status()

    with open(path, "wb") as f:
        f.write(r.content)

    return path

def unzip_file(zip_path):
    folder = zip_path.replace(".zip", "")
    os.makedirs(folder, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(folder)
    return folder

# ========= CV =========

def read_pdf(path):
    doc = fitz.open(path)
    text = ""
    for p in doc:
        text += p.get_text()
    return text

def get_all_files(folder):
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            if f.endswith(".pdf"):
                files.append(os.path.join(root, f))
    return files

def read_skills():
    with open(SKILLS_PATH, "r", encoding="utf-8") as f:
        return f.read()

# ========= LLM =========

def ask_llm(prompt):
    res = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen3.5",
            "prompt": prompt,
            "stream": False
        }
    )
    return res.json()["response"]

def build_prompt(cv_text, skills_text):
    return f"""
# Task: CV Reconstruction & Professional Evaluation

Evaluate based on:
{skills_text}

---
{cv_text}

Output:
- Score (/10)
- Recommendation
- Key strengths
- Key weaknesses
"""

# ========= TELEGRAM =========

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    )

# ========= MAIN =========

def run():
    skills = read_skills()

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, '(UNSEEN SUBJECT "Resume Download")')
    email_ids = messages[0].split()[-5:]

    for eid in email_ids:
        _, data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        subject = decode_mime_words(msg.get("Subject"))

        if "Resume Download" not in subject:
            continue

        print("Processing:", subject)

        links = extract_links(msg)

        for link in links:
            zip_path = download_zip(link)
            folder = unzip_file(zip_path)

            files = get_all_files(folder)

            for file in files:
                cv_text = read_pdf(file)[:15000]

                prompt = build_prompt(cv_text, skills)
                result = ask_llm(prompt)

                print(result)

                # 👉 簡單 rule：只推 INTERVIEW / HIRE
                if "INTERVIEW" in result or "HIRE" in result:
                    send_telegram(f"🔥 Candidate Alert\n{file}\n\n{result[:500]}")

        mail.store(eid, '+FLAGS', '\\Seen')

    mail.logout()

if __name__ == "__main__":
    run()
