import os
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

import config
from common import (
    init_db, ensure_dir, forum_page_url, topic_page_url, get_html,
    extract_topics_from_forum_page, topic_passes_date_filter,
    extract_posts_from_topic_page
)


def save_topic(cur, topic):
    cur.execute("""
        INSERT OR REPLACE INTO topics
        (topic_id, title, slug, author, replies, views, last_page, first_post_date, source_forum_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        topic["topic_id"], topic["title"], topic["slug"], topic["author"],
        topic["replies"], topic["views"], topic["last_page"],
        topic.get("first_post_date", ""), topic["source_forum_url"]
    ))


def load_topics(cur):
    topics = {}
    rows = cur.execute("""
        SELECT topic_id, title, slug, author, replies, views, last_page, first_post_date, source_forum_url
        FROM topics
    """).fetchall()
    for row in rows:
        topic_id, title, slug, author, replies, views, last_page, first_post_date, source_forum_url = row
        topics[topic_id] = {
            "topic_id": topic_id,
            "title": title,
            "slug": slug,
            "author": author,
            "replies": replies,
            "views": views,
            "last_page": last_page,
            "first_post_date": first_post_date or "",
            "source_forum_url": source_forum_url,
        }
    return topics


def main():
    if config.RESET_BEFORE_CRAWL:
        print("RESET_BEFORE_CRAWL=True : nettoyage sortie.")
        shutil.rmtree(config.OUT, ignore_errors=True)

    ensure_dir(config.OUT)
    db_path = os.path.join(config.OUT, "jol_archive.db")
    conn = init_db(db_path)
    cur = conn.cursor()

    print(f"Crawl des pages forum {config.FORUM_PAGE_START} à {config.FORUM_PAGE_END}")

    for forum_page in tqdm(range(config.FORUM_PAGE_START, config.FORUM_PAGE_END + 1), desc="Forum"):
        done = cur.execute(
            "SELECT done FROM crawl_forum_pages WHERE page_num=?",
            (forum_page,)
        ).fetchone()
        if done and done[0] == 1:
            continue

        url = forum_page_url(forum_page)
        html_text = get_html(url)
        if not html_text:
            print("Échec page forum :", url)
            continue

        topics = extract_topics_from_forum_page(html_text, url)
        for topic in topics.values():
            save_topic(cur, topic)

        # Important reprise : on marque la page forum terminée seulement APRÈS avoir enregistré ses topics.
        cur.execute("INSERT OR REPLACE INTO crawl_forum_pages(page_num, done) VALUES (?, 1)", (forum_page,))
        conn.commit()
        time.sleep(config.WAIT_FORUM_PAGES)

    all_topics = load_topics(cur)
    print("Topics connus dans la DB :", len(all_topics))

    selected = {}
    for topic_id, topic in tqdm(list(all_topics.items()), desc="Filtrage"):
        ok, topic = topic_passes_date_filter(topic)
        if not ok:
            continue

        if config.ASK_BIG_TOPICS and topic["last_page"] > config.BIG_TOPIC_THRESHOLD:
            print("\nGros topic détecté :")
            print(f"- {topic['title']}")
            print(f"- Topic ID : {topic_id}")
            print(f"- Pages : {topic['last_page']}")
            if topic.get("first_post_date"):
                print(f"- Premier post : {topic['first_post_date']}")
            ans = input("L'enregistrer ? y/n : ").strip().lower()
            if ans not in ["y", "yes", "o", "oui"]:
                continue

        selected[topic_id] = topic
        save_topic(cur, topic)

    conn.commit()
    print("Topics sélectionnés :", len(selected))

    topic_pages = []
    for topic_id, topic in selected.items():
        for page_num in range(1, topic["last_page"] + 1):
            row = cur.execute(
                "SELECT done FROM crawl_topic_pages WHERE topic_id=? AND page_num=?",
                (topic_id, page_num)
            ).fetchone()
            if row and row[0] == 1:
                continue

            url = topic_page_url(topic_id, topic["slug"], page_num)
            cur.execute("""
                INSERT OR IGNORE INTO crawl_topic_pages(topic_id, page_num, url, done)
                VALUES (?, ?, ?, 0)
            """, (topic_id, page_num, url))
            topic_pages.append((topic_id, page_num, url))

    conn.commit()
    print("Pages topics à traiter :", len(topic_pages))

    def fetch(item):
        topic_id, page_num, url = item
        return topic_id, page_num, url, get_html(url)

    done_count = 0
    with ThreadPoolExecutor(max_workers=config.HTML_WORKERS) as ex:
        futures = [ex.submit(fetch, item) for item in topic_pages]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Topics"):
            topic_id, page_num, url, html_text = fut.result()
            if not html_text:
                print("Échec topic :", url)
                continue

            extract_posts_from_topic_page(cur, topic_id, page_num, html_text, url)
            cur.execute("""
                INSERT OR REPLACE INTO crawl_topic_pages(topic_id, page_num, url, done)
                VALUES (?, ?, ?, 1)
            """, (topic_id, page_num, url))

            done_count += 1
            if done_count % 50 == 0:
                conn.commit()

    conn.commit()
    print("Crawl terminé.")
    print("DB :", os.path.abspath(db_path))
    print("Topics :", cur.execute("SELECT COUNT(*) FROM topics").fetchone()[0])
    print("Posts :", cur.execute("SELECT COUNT(*) FROM posts").fetchone()[0])
    print("Assets en attente :", cur.execute("SELECT COUNT(*) FROM pending_assets").fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main()
