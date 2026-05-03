import os
import re
import html
import sqlite3
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
    return f"{prefix}topic/{topic_id}/{page_num}.html#post{post_id}"

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

STYLE = """
body { font-family: Arial, sans-serif; background:#f4f0e5; color:#222; margin:0; }
header { background:#6b3f1d; color:white; padding:16px 24px; }
main { max-width:1200px; margin:20px auto; padding:0 16px; }
a { color:#8a2500; text-decoration:none; }
a:hover { text-decoration:underline; }
.topic, .post { background:white; border:1px solid #d8c7a8; border-radius:8px; padding:14px; margin:12px 0; }
.meta { color:#666; font-size:13px; margin-top:4px; }
.post { display:flex; gap:14px; }
.avatar { width:90px; flex:0 0 90px; }
.avatar img { max-width:80px; max-height:80px; border-radius:6px; border:1px solid #ccc; background:#eee; }
.post-body { flex:1; min-width:0; }
.post-author { font-weight:bold; margin-bottom:6px; }
.nav { margin:16px 0; }
img { max-width:100%; height:auto; }
.inline-linked-image { display:block; max-width:700px; margin:8px 0; border:1px solid #ccc; border-radius:6px; }
.gallery { display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:12px; }
.tile { background:white; border:1px solid #d8c7a8; border-radius:8px; padding:8px; overflow:hidden; }
.tile img { width:100%; height:160px; object-fit:contain; background:#eee; }
.small { font-size:12px; color:#666; word-break:break-all; margin-top:6px; }
"""

def main():
    db_path = os.path.join(config.OUT, "jol_archive.db")
    conn = init_db(db_path)
    cur = conn.cursor()

    site = os.path.join(config.OUT, "site")
    ensure_dir(site)
    write_file(os.path.join(site, "style.css"), STYLE)

    asset_map = {row[0]: row[1] for row in cur.execute("SELECT original_url, local_path FROM assets").fetchall()}
    sanitize_fragment = make_sanitizer(asset_map)

    topics_rows = cur.execute("""
        SELECT topic_id, title, author, replies, views, last_page, first_post_date
        FROM topics ORDER BY topic_id DESC
    """).fetchall()

    index = """<!doctype html><html><head><meta charset="utf-8"><title>Archive JOL</title><link rel="stylesheet" href="style.css"></head><body><header><h1>Archive JOL — Dofus</h1></header><main><p><a href="images.html">Mosaïque images</a> — <a href="avatars.html">Mosaïque avatars</a></p>"""

    for topic_id, title, author, replies, views, last_page, first_post_date in topics_rows:
        index += f"""
        <div class="topic">
          <a href="topic/{topic_id}/1.html"><strong>{html.escape(title or "")}</strong></a>
          <div class="meta">par {html.escape(author or "?")} — {replies} réponses — {views} vues — {last_page} page(s) — premier post : {html.escape(first_post_date or "?")}</div>
        </div>
        """

    index += "</main></body></html>"
    write_file(os.path.join(site, "index.html"), index)

    for topic_id, title, slug, author, replies, views, last_page, first_post_date in cur.execute("""
        SELECT topic_id, title, slug, author, replies, views, last_page, first_post_date FROM topics
    """).fetchall():

        original_topic_url = topic_page_url(topic_id, slug, 1)

        for page_num in range(1, last_page + 1):
            posts = cur.execute("""
                SELECT post_id, author, avatar_local_path, date_text, content_html
                FROM posts WHERE topic_id=? AND page_num=? ORDER BY post_id
            """, (topic_id, page_num)).fetchall()

            page_url = topic_page_url(topic_id, slug, page_num)

            page = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title or "")} — page {page_num}</title><link rel="stylesheet" href="../../style.css"></head><body><header><h1>{html.escape(title or "")}</h1></header><main><div class="nav"><a href="../../index.html">← Retour index</a></div><div class="meta">Sujet {topic_id} — page {page_num}/{last_page} — premier post : {html.escape(first_post_date or "?")}</div><div class="nav"><a href="{html.escape(original_topic_url)}">Voir le topic original sur JeuxOnline</a></div><div class="nav">"""

            if page_num > 1:
                page += f'<a href="{page_num - 1}.html">← Page précédente</a> '
            if page_num < last_page:
                page += f'<a href="{page_num + 1}.html">Page suivante →</a>'
            page += "</div>"

            for post_id, post_author, avatar_local, date_text, content_html in posts:
                fixed = sanitize_fragment(content_html, page_url, "../../../")
                avatar_html = ""
                if avatar_local:
                    avatar_html = f'<img src="{html.escape(site_asset_path(avatar_local, "../../../"))}" alt="avatar" loading="lazy">'

                page += f"""
                <article class="post" id="post{post_id}">
                  <div class="avatar">{avatar_html}</div>
                  <div class="post-body">
                    <div class="post-author">{html.escape(post_author or "?")}</div>
                    <div class="meta">{html.escape(date_text or "")} — post #{post_id} — <a href="{html.escape(jol_post_url(post_id))}">original JOL</a></div>
                    <div>{fixed}</div>
                  </div>
                </article>
                """

            page += "</main></body></html>"
            write_file(os.path.join(site, "topic", str(topic_id), f"{page_num}.html"), page)

    avatar_paths = set(row[0] for row in cur.execute("""
        SELECT DISTINCT avatar_local_path FROM posts WHERE avatar_local_path IS NOT NULL AND avatar_local_path != ''
    """).fetchall())

    assets_rows = cur.execute("SELECT original_url, local_path FROM assets ORDER BY local_path").fetchall()
    topic_images, avatar_images = [], []

    for original_url, rel in assets_rows:
        if not rel:
            continue
        if rel in avatar_paths:
            avatar_images.append((original_url, rel))
        else:
            topic_images.append((original_url, rel))

    def first_usage(original_url):
        return cur.execute("""
            SELECT topic_id, page_num, post_id FROM asset_usages
            WHERE original_url=? ORDER BY topic_id, page_num, post_id LIMIT 1
        """, (original_url,)).fetchone()

    def gallery(title, images, avatars=False):
        page = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title><link rel="stylesheet" href="style.css"></head><body><header><h1>{html.escape(title)}</h1></header><main><div class="nav"><a href="index.html">← Retour index</a></div><p>{len(images)} image(s)</p><div class="gallery">"""
        for original_url, rel in images:
            src = html.escape("../" + rel)
            usage_html = ""
            if not avatars:
                u = first_usage(original_url)
                if u:
                    topic_id, page_num, post_id = u
                    usage_html = f'<div class="small"><a href="{html.escape(local_post_url(topic_id, page_num, post_id))}">Voir le premier post local utilisant cette image</a></div>'
            page += f"""<div class="tile"><a href="{src}"><img src="{src}" loading="lazy" alt=""></a>{usage_html}<div class="small">{html.escape(original_url or "")}</div></div>"""
        page += "</div></main></body></html>"
        return page

    write_file(os.path.join(site, "images.html"), gallery("Mosaïque des images des topics", topic_images, False))
    write_file(os.path.join(site, "avatars.html"), gallery("Mosaïque des avatars", avatar_images, True))

    print("Mini-site généré :", site)
    print("Images topics :", len(topic_images))
    print("Avatars :", len(avatar_images))
    conn.close()

if __name__ == "__main__":
    main()
