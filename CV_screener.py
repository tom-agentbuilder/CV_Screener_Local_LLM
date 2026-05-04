import imaplib
import email
import re
import os
import requests
import zipfile
from email.header import decode_header
from datetime import datetime

# ========= CONFIG =========
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

DOWNLOAD_DIR = r"C:\Users\user\Downloads"

DOWNLOADED_ZIPS = []
SHORTLIST = {}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


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


def extract_links_from_email(msg):
    links = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                try:
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    links += re.findall(r'https?://[^\s"<>]+', body)
                except:
                    pass
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")
        links += re.findall(r'https?://[^\s"<>]+', body)

    return [l for l in links if ".zip" in l]


def download_zip(url, save_dir):
    try:
        filename = url.split("/")[-1].split("?")[0]
        save_path = os.path.join(save_dir, filename)

        print(f"Downloading: {filename}")

        r = requests.get(url, timeout=60)
        r.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(r.content)

        return save_path

    except Exception as e:
        print("Download failed:", e)
        return None


def unzip_file(zip_path):
    try:
        extract_dir = zip_path.replace(".zip", "")
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)

        return extract_dir

    except Exception as e:
        print("Unzip failed:", e)
        return None


def run_pipeline():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, '(UNSEEN SUBJECT "Resume Download")')
    email_ids = messages[0].split()[-10:]

    for eid in email_ids:
        status, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject = decode_mime_words(msg.get("Subject"))
        if "Resume Download" not in subject:
            continue

        links = extract_links_from_email(msg)

        for link in links:
            zip_path = download_zip(link, DOWNLOAD_DIR)

            if zip_path:
                DOWNLOADED_ZIPS.append(zip_path)
                unzip_file(zip_path)

        mail.store(eid, '+FLAGS', '\\Seen')

    mail.logout()


# ========= CV PROCESS =========

import fitz

def read_pdf_better(path):
    try:
        doc = fitz.open(path)
        return "".join([p.get_text() for p in doc])
    except:
        return ""


def read_cv(path):
    return read_pdf_better(path) if path.endswith(".pdf") else ""


def get_all_files(folder):
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            if f.endswith((".pdf", ".docx")):
                files.append(os.path.join(root, f))
    return files


def read_skills(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def ask_llm(prompt):
    res = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen3.5", "prompt": prompt, "stream": False}
    )
    return res.json()["response"]


# ========= KEEP YOUR PROMPT =========

def build_prompt(cv_text, skills_text):
    current_date = datetime.now().strftime("%d %B %Y")

    return f"""
# Task: CV Reconstruction & Professional Evaluation
...
Today is {current_date}.
"""


# ========= TELEGRAM =========

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except Exception as e:
        print("Telegram error:", e)
