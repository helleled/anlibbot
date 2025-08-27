import requests
import feedparser
import os
import json
import time
import re
from html import unescape
from datetime import datetime, timedelta

# Misskey API 설정
MISSKEY_URL = "https://it.21stcentury.day"
API_TOKEN = "NX2YWgEHHV4iUIARk0rhUhqDA8ttvzjm"

# 텍스트 제한 함수
def truncate_text(text, max_length=3000):
    if len(text) > max_length:
        return text[:300] + "..."
    return text

def strip_html_tags(text):
    # HTML 태그 제거
    clean = re.sub(r'<.*?>', '', text)
    # HTML 엔티티를 일반문자로 변환
    return unescape(clean)

# CW로 노트 게시
def post_to_misskey_with_cw(cw_text, note_content):
    url = f"{MISSKEY_URL}/api/notes/create"
    headers = {
        "Content-Type": "application/json",
    }
    note_content = truncate_text(strip_html_tags(note_content))
    payload = {
        "i": API_TOKEN,
        "text": note_content,  # 본문
        "cw": cw_text,         # CW 제목
    }
    response = requests.post(url, json=payload, headers=headers)

    # 응답 확인
    if response.status_code == 200:
        print("Note posted successfully with CW!")
    else:
        print(f"Failed to post note: {response.status_code} - {response.text}")


# RSS 피드 가져오기
def fetch_recent_rss_feed(url):
    feed = feedparser.parse(url)
    entries = []

    now = datetime.now()

    for entry in feed.entries:
        try:
            if 'published' in entry:
                entry_date = datetime(*entry.published_parsed[:6])
            elif 'updated' in entry:
                entry_date = datetime(*entry.updated_parsed[:6])
            else:
                continue
        except (AttributeError, ValueError):
            continue

        if now - entry_date < timedelta(days=1):
            entries.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary,
                "date": entry_date
            })

    return entries

def process_rss_feed(url):
    posted_entries = load_posted_entries()
    new_entries = fetch_recent_rss_feed(url)

    for entry in new_entries:
        if entry["link"] not in posted_entries:
            cw_text = f"새 글: {entry['title']}"
            note_content = (
                f"🔗 {entry['link']}\n\n"
                f"{entry['summary']}"
            )

            post_to_misskey_with_cw(cw_text, note_content)

            posted_entries.append(entry["link"])
            save_posted_entries(posted_entries)


# 이미 게시된 항목 추적
POSTED_ENTRIES_FILE = "posted_entries.json"

def load_posted_entries():
    if os.path.exists(POSTED_ENTRIES_FILE):
        with open(POSTED_ENTRIES_FILE, "r") as file:
            return json.load(file)
    return []

def save_posted_entries(entries):
    with open(POSTED_ENTRIES_FILE, "w") as file:
        json.dump(entries, file)

# RSS URL 선언
rss_url = "https://theanarchistlibrary.org/feed"

# 반복 실행
while True:
    process_rss_feed(rss_url)
    time.sleep(3600)  # 1시간 대기
