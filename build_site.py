import os
import html
import sqlite3
import json
from bs4 import BeautifulSoup

import config
from common import init_db, normalize_url, is_direct_image_url, topic_page_url, ensure_dir

def write_file(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def jol_post_url(post_id):
    return f"https://forums.jeuxonline.info/p/{post_id}#post{post_id}"

def site_asset_path(rel_path, prefix):
    return prefix + rel_path.replace("\\", "/") if rel_path else ""

def local_post_url(topic_id, page_num, post_id, prefix=""):
    return f"{prefix}topic.html?topic_id={topic_id}&page={page_num}#post{post_id}"

def make_sanitizer(asset_map):
    def sanitize_fragment(fragment, page_url, prefix):
        soup = BeautifulSoup(fragment or "", "html.parser")

        # Pas de contenu actif.
        for tag in soup.find_all(["script", "style", "iframe", "object", "embed", "form", "input", "button", "link", "meta"]):
            tag.decompose()

        # Supprime l'ancien bloc auteur/avatar de JOL : on a notre colonne propre.
        for tag in soup.find_all(class_=lambda c: c and (
            "message-author" in c or "responsive-avatar" in c or "message-avatar" in c or "message-after-avatar" in c
        )):
            tag.decompose()

        for tag in soup.find_all(class_=lambda c: c and ("jol-user-title" in c or "jol-nt" in c)):
            tag.decompose()

        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if attr.lower().startswith("on"):
                    del tag.attrs[attr]

            if tag.name in ["img", "source"]:
                raw = tag.get("data-src") or tag.get("src")
                full = normalize_url(raw, page_url)
                if full in asset_map:
                    tag["src"] = site_asset_path(asset_map[full], prefix)
                if tag.has_attr("data-src"):
                    del tag["data-src"]

            if tag.name == "a":
                href = tag.get("href", "")
                if href.startswith("javascript:"):
                    del tag.attrs["href"]
                    continue

                full = normalize_url(href, page_url)
                if full in asset_map:
                    local = site_asset_path(asset_map[full], prefix)
                    tag["href"] = local
                    if is_direct_image_url(full):
                        img = soup.new_tag("img", src=local)
                        img["class"] = "inline-linked-image"
                        img["loading"] = "lazy"
                        tag.clear()
                        tag.append(img)

        return str(soup)
    return sanitize_fragment

def main():
    db_path = os.path.join(config.OUT, "jol_archive.db")
    conn = init_db(db_path)
    cur = conn.cursor()

    site = os.path.join(os.path.dirname(__file__), "templates", "site")
    ensure_dir(site)

    asset_map = {row[0]: row[1] for row in cur.execute("SELECT original_url, local_path FROM assets").fetchall()}
    sanitize_fragment = make_sanitizer(asset_map)

    topics_rows = cur.execute("""
        SELECT topic_id, title, author, replies, views, last_page, first_post_date, source_forum_url
        FROM topics ORDER BY topic_id DESC
    """).fetchall()

    topics_data = [
        {
            "topic_id": topic_id, "title": title or "", "author": author or "",
            "replies": replies or 0, "views": views or 0, "last_page": last_page or 1,
            "first_post_date": first_post_date or "",
            "source_forum_url": source_forum_url or ""
        }
        for topic_id, title, author, replies, views, last_page, first_post_date, source_forum_url in topics_rows
    ]
    write_file(os.path.join(site, "topics.js"), "window.TOPICS_DATA = " + json.dumps(topics_data, ensure_ascii=False) + ";")

    for topic_id, title, slug, author, replies, views, last_page, first_post_date, source_forum_url in cur.execute("""
        SELECT topic_id, title, slug, author, replies, views, last_page, first_post_date, source_forum_url FROM topics
    """).fetchall():

        original_topic_url = topic_page_url(topic_id, slug, 1)

        for page_num in range(1, last_page + 1):
            posts = cur.execute("""
                SELECT post_id, author, avatar_local_path, date_text, content_html
                FROM posts WHERE topic_id=? AND page_num=? ORDER BY post_id
            """, (topic_id, page_num)).fetchall()

            page_url = topic_page_url(topic_id, slug, page_num)
            export_posts = []
            for post_id, post_author, avatar_local, date_text, content_html in posts:
                fixed = sanitize_fragment(content_html, page_url, "../../")
                export_posts.append({
                    "post_id": post_id,
                    "author": post_author or "",
                    "avatar_local_path": site_asset_path(avatar_local, "../../") if avatar_local else "",
                    "date_text": date_text or "",
                    "content_html": fixed,
                })

            topic_payload = {
                "topic_id": topic_id,
                "title": title or "",
                "author": author or "",
                "replies": replies or 0,
                "views": views or 0,
                "last_page": last_page or 1,
                "first_post_date": first_post_date or "",
            "source_forum_url": source_forum_url or "",
                "page_num": page_num,
                "original_topic_url": original_topic_url,
                "posts": export_posts,
            }
            write_file(os.path.join(site, "topic_data", str(topic_id), f"{page_num}.json"), json.dumps(topic_payload, ensure_ascii=False))

    avatar_paths = set(row[0] for row in cur.execute("""
        SELECT DISTINCT avatar_local_path FROM posts WHERE avatar_local_path IS NOT NULL AND avatar_local_path != ''
    """).fetchall())

    assets_rows = cur.execute("SELECT original_url, local_path FROM assets ORDER BY local_path").fetchall()
    topic_images, avatar_images = [], []

    missing_gallery_assets = 0
    for original_url, rel in assets_rows:
        if not rel:
            continue
        abs_asset = os.path.join(config.OUT, rel)
        if not os.path.exists(abs_asset):
            missing_gallery_assets += 1
            continue
        if rel in avatar_paths:
            avatar_images.append((original_url, rel))
        else:
            topic_images.append((original_url, rel))

    def first_usage(original_url):
        row = cur.execute("""
            SELECT topic_id, page_num, post_id FROM asset_usages
            WHERE original_url=? ORDER BY topic_id, page_num, post_id LIMIT 1
        """, (original_url,)).fetchone()
        if not row:
            return None
        return {"topic_id": row[0], "page_num": row[1], "post_id": row[2]}

    def gallery_payload(images, avatars=False):
        payload = []
        for original_url, rel in images:
            item = {"original_url": original_url or "", "local_path": rel, "first_usage": None}
            if not avatars:
                item["first_usage"] = first_usage(original_url)
            payload.append(item)
        return payload

    write_file(os.path.join(site, "galleries", "images.json"), json.dumps(gallery_payload(topic_images, False), ensure_ascii=False))
    write_file(os.path.join(site, "galleries", "avatars.json"), json.dumps(gallery_payload(avatar_images, True), ensure_ascii=False))

    print("HTML templates utilisés directement :", site)
    print("Images topics :", len(topic_images))
    print("Avatars :", len(avatar_images))
    print("Assets introuvables ignorés en galerie :", missing_gallery_assets)
    conn.close()

if __name__ == "__main__":
    main()
