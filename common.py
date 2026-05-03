import os
import re
import time
import html
import sqlite3
import hashlib
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup, NavigableString

import config

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def forum_page_url(page_num):
    if page_num == 1:
        return f"{config.BASE}/forum/{config.FORUM_ID}/{config.FORUM_SLUG}"
    return f"{config.BASE}/forum/{config.FORUM_ID}---{page_num}/{config.FORUM_SLUG}"

def topic_page_url(topic_id, slug, page_num):
    if page_num == 1:
        return f"{config.BASE}/sujet/{topic_id}/{slug}"
    return f"{config.BASE}/sujet/{topic_id}-{page_num}/{slug}"

def normalize_url(url, page_url="https://forums.jeuxonline.info"):
    if not url:
        return ""

    try:
        url = str(url).strip()

        if not url:
            return ""

        if url.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
            return ""

        if url.startswith("//"):
            url = "https:" + url
        else:
            url = urljoin(page_url, url)

        url, _ = urldefrag(url)
        return url

    except Exception:
        return ""

def get_html(url, timeout=25):
    try:
        r = requests.get(url, headers=config.HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None

def clean_int(txt):
    if not txt:
        return 0
    txt = txt.replace("\xa0", "").replace(" ", "")
    txt = re.sub(r"[^\d]", "", txt)
    return int(txt) if txt else 0

def is_direct_image_url(url):
    return urlparse(url.lower()).path.endswith(IMAGE_EXTENSIONS)

def parse_fr_date(date_text):
    if not date_text:
        return None
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", date_text)
    if not m:
        return None
    return datetime.strptime(m.group(1) + "/" + m.group(2) + "/" + m.group(3), "%d/%m/%Y").date()

def parse_filter_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%d/%m/%Y").date()

def init_db(db_path):
    ensure_dir(os.path.dirname(db_path))
    conn = sqlite3.connect(db_path, timeout=60)
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;
    PRAGMA temp_store=MEMORY;
    PRAGMA cache_size=-100000;

    CREATE TABLE IF NOT EXISTS topics (
        topic_id INTEGER PRIMARY KEY,
        title TEXT,
        slug TEXT,
        author TEXT,
        replies INTEGER,
        views INTEGER,
        last_page INTEGER,
        first_post_date TEXT,
        source_forum_url TEXT
    );

    CREATE TABLE IF NOT EXISTS posts (
        post_id INTEGER PRIMARY KEY,
        topic_id INTEGER,
        page_num INTEGER,
        author TEXT,
        avatar_original_url TEXT,
        avatar_local_path TEXT,
        date_text TEXT,
        content_html TEXT,
        content_text TEXT
    );

    CREATE TABLE IF NOT EXISTS pending_assets (
        original_url TEXT PRIMARY KEY,
        asset_type TEXT,
        found_in TEXT
    );

    CREATE TABLE IF NOT EXISTS asset_usages (
        original_url TEXT,
        topic_id INTEGER,
        page_num INTEGER,
        post_id INTEGER,
        PRIMARY KEY(original_url, topic_id, page_num, post_id)
    );

    CREATE TABLE IF NOT EXISTS crawl_forum_pages (
        page_num INTEGER PRIMARY KEY,
        done INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS crawl_topic_pages (
        topic_id INTEGER,
        page_num INTEGER,
        url TEXT,
        done INTEGER DEFAULT 0,
        PRIMARY KEY(topic_id, page_num)
    );

    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_url TEXT UNIQUE,
        local_path TEXT,
        sha1 TEXT,
        asset_type TEXT
    );
    """)
    conn.commit()
    return conn

def queue_asset(cur, url, asset_type="image", found_in="post", topic_id=None, page_num=None, post_id=None):
    url = normalize_url(url)
    if not url or url.startswith("data:"):
        return

    low = url.lower()
    if not is_direct_image_url(url) and "jolstatic.fr" not in low and "customavatars" not in low and "customprofilepics" not in low:
        return

    cur.execute("""
        INSERT OR IGNORE INTO pending_assets(original_url, asset_type, found_in)
        VALUES (?, ?, ?)
    """, (url, asset_type, found_in))

    if topic_id and page_num and post_id and asset_type != "avatar":
        cur.execute("""
            INSERT OR IGNORE INTO asset_usages(original_url, topic_id, page_num, post_id)
            VALUES (?, ?, ?, ?)
        """, (url, topic_id, page_num, post_id))

def asset_local_rel(url):
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if not ext or len(ext) > 8:
        ext = ".bin"
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return os.path.join("assets", h[:2], h + ext).replace("\\", "/")

def extract_topics_from_forum_page(html_text, forum_url):
    soup = BeautifulSoup(html_text, "html.parser")
    # Pas de .select ici : compatible Python 3.14 / SoupSieve capricieux.
    thread_container = soup.find("tbody", id=f"threadbits_forum_{config.FORUM_ID}")
    topics = {}

    if not thread_container:
        return topics

    for row in thread_container.find_all("tr"):
        classes = row.get("class", [])
        if "jol-threadlist-line" not in classes:
            continue
        if not row.get("data-jol-discussion-id"):
            continue

        a = row.find("a", id=re.compile(r"^thread_title_\d+"))
        if not a or not a.get("href"):
            continue

        full = normalize_url(a["href"], config.BASE)
        m = re.search(r"/sujet/(\d+)(?:-\d+)?/(.+)", full)
        if not m:
            continue

        topic_id = int(m.group(1))
        slug = m.group(2).split("#")[0]
        title = a.get_text(" ", strip=True)

        author = ""
        author_el = row.find(class_="jol-threadlist-starter")
        if author_el:
            author = author_el.get_text(" ", strip=True)

        replies = 0
        reply_el = row.find(class_="jol-thread-replycount")
        if reply_el:
            replies = clean_int(reply_el.get_text(" ", strip=True))

        views = 0
        reply_cell = row.find("td", class_=lambda c: c and "threadlistreply" in c)
        if reply_cell and reply_cell.get("title"):
            m_views = re.search(r"([\d\s\xa0]+)\s+affichages", reply_cell["title"])
            if m_views:
                views = clean_int(m_views.group(1))

        last_page = max(1, (replies + 1 + 24) // 25)
        last_a = row.find("a", class_=lambda c: c and "jol-thread-lastpage" in c)
        if last_a and last_a.get("href"):
            m2 = re.search(r"/sujet/\d+-(\d+)/", last_a["href"])
            if m2:
                last_page = max(last_page, int(m2.group(1)))

        topics[topic_id] = {
            "topic_id": topic_id,
            "slug": slug,
            "title": title,
            "author": author,
            "replies": replies,
            "views": views,
            "last_page": last_page,
            "first_post_date": "",
            "source_forum_url": forum_url,
        }

    return topics

def get_first_post_date_from_topic_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    first_post = soup.find("table", id=re.compile(r"^post\d+")) or soup.find(id=re.compile(r"^post\d+"))
    if not first_post:
        return ""

    date_el = first_post.find(class_="post-datetime")
    if date_el:
        return date_el.get_text(" ", strip=True)

    text_all = first_post.get_text(" ", strip=True)
    m = re.search(r"\d{2}/\d{2}/\d{4}.*?\d{1,2}h\d{2}", text_all)
    return m.group(0) if m else ""

def collect_assets_in_fragment(cur, fragment, page_url, topic_id=None, page_num=None, post_id=None):
    soup = BeautifulSoup(fragment or "", "html.parser")

    for tag in soup.find_all(["img", "source"]):
        src = tag.get("data-src") or tag.get("src")
        if src:
            queue_asset(cur, normalize_url(src, page_url), "image", "post", topic_id, page_num, post_id)

    for a in soup.find_all("a", href=True):
        href = normalize_url(a["href"], page_url)
        if is_direct_image_url(href):
            queue_asset(cur, href, "image", "post_link", topic_id, page_num, post_id)

    url_regex = re.compile(
        r"https?://[^\s<>'\"]+\.(?:jpg|jpeg|png|gif|webp|bmp|svg)(?:\?[^\s<>'\"]*)?",
        re.I
    )
    for m in url_regex.finditer(soup.get_text(" ")):
        queue_asset(cur, m.group(0), "image", "text_url", topic_id, page_num, post_id)

    return str(soup)

def extract_avatar_from_post_node(cur, node, page_url):
    for img in node.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if not src:
            continue
        full = normalize_url(src, page_url)
        low = full.lower()
        if "avatar" in low or "customavatars" in low or "customprofilepics" in low:
            queue_asset(cur, full, "avatar", "avatar")
            return full, ""
    return "", ""

def extract_posts_from_topic_page(cur, topic_id, page_num, html_text, page_url):
    soup = BeautifulSoup(html_text, "html.parser")
    posts_found = 0

    candidates = soup.find_all("table", id=re.compile(r"^post\d+"))
    if not candidates:
        candidates = soup.find_all(id=re.compile(r"^post\d+"))

    seen_post_ids = set()

    for node in candidates:
        node_id = node.get("id", "")
        m = re.search(r"post(\d+)", node_id)
        if not m:
            continue

        post_id = int(m.group(1))
        if post_id in seen_post_ids:
            continue
        seen_post_ids.add(post_id)

        text_all = node.get_text(" ", strip=True)
        if len(text_all) < 20:
            continue

        author = ""
        author_el = node.find(class_="bigusername") or node.find(class_="username")
        if not author_el:
            author_el = node.find("a", href=re.compile(r"/auteur/"))
        if author_el:
            author = author_el.get_text(" ", strip=True)

        avatar_original, avatar_local = extract_avatar_from_post_node(cur, node, page_url)

        date_text = ""
        date_el = node.find(class_="post-datetime")
        if date_el:
            date_text = date_el.get_text(" ", strip=True)
        else:
            date_match = re.search(r"\d{2}/\d{2}/\d{4}.*?\d{1,2}h\d{2}", text_all)
            if date_match:
                date_text = date_match.group(0)

        content_node = node.find(id=f"post_message_{post_id}")
        if not content_node:
            content_node = node.find(class_="post_message") or node.find(class_="message-body") or node

        content_html = collect_assets_in_fragment(cur, str(content_node), page_url, topic_id, page_num, post_id)
        content_text = BeautifulSoup(content_html, "html.parser").get_text("\n", strip=True)

        if len(content_text) < 10:
            continue

        cur.execute("""
            INSERT OR REPLACE INTO posts
            (post_id, topic_id, page_num, author, avatar_original_url, avatar_local_path, date_text, content_html, content_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (post_id, topic_id, page_num, author, avatar_original, avatar_local, date_text, content_html, content_text))

        posts_found += 1

    return posts_found

def topic_passes_date_filter(topic):
    start = parse_filter_date(config.FIRST_POST_DATE_START)
    end = parse_filter_date(config.FIRST_POST_DATE_END)
    if not start and not end:
        return True, topic

    first_url = topic_page_url(topic["topic_id"], topic["slug"], 1)
    html_text = get_html(first_url)
    if not html_text:
        return False, topic

    first_date_text = get_first_post_date_from_topic_html(html_text)
    topic["first_post_date"] = first_date_text

    first_date = parse_fr_date(first_date_text)
    if not first_date:
        return False, topic
    if start and first_date < start:
        return False, topic
    if end and first_date > end:
        return False, topic
    return True, topic
