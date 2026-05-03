import os
import hashlib
import sqlite3
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from common import init_db, normalize_url, is_direct_image_url, asset_local_rel, ensure_dir

def download_one(url):
    url = normalize_url(url)
    try:
        r = requests.get(url, headers=config.HEADERS, timeout=30)
        if r.status_code != 200:
            return None

        content_type = r.headers.get("content-type", "").lower()
        if not (content_type.startswith("image/") or is_direct_image_url(url)):
            return None

        rel = asset_local_rel(url)
        local = os.path.join(config.OUT, rel)
        ensure_dir(os.path.dirname(local))

        # Même URL = même fichier. Si déjà là, ne réécrit pas.
        if not os.path.exists(local):
            with open(local, "wb") as f:
                f.write(r.content)

        sha1 = hashlib.sha1(r.content).hexdigest()
        return url, rel, sha1
    except Exception:
        return None

def main():
    db_path = os.path.join(config.OUT, "jol_archive.db")
    conn = init_db(db_path)
    cur = conn.cursor()

    urls = [row[0] for row in cur.execute("""
        SELECT original_url FROM pending_assets
        WHERE original_url NOT IN (SELECT original_url FROM assets)
    """).fetchall()]

    print("Assets à télécharger :", len(urls))

    inserted = 0
    with ThreadPoolExecutor(max_workers=config.ASSET_WORKERS) as ex:
        futures = [ex.submit(download_one, url) for url in urls]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Assets"):
            result = fut.result()
            if not result:
                continue

            original_url, rel_path, sha1 = result
            row = cur.execute("SELECT asset_type FROM pending_assets WHERE original_url=?", (original_url,)).fetchone()
            asset_type = row[0] if row else "image"

            cur.execute("""
                INSERT OR IGNORE INTO assets(original_url, local_path, sha1, asset_type)
                VALUES (?, ?, ?, ?)
            """, (original_url, rel_path, sha1, asset_type))

            inserted += 1
            if inserted % 500 == 0:
                conn.commit()

    conn.commit()

    # Lie les avatars aux posts
    avatar_rows = cur.execute("""
        SELECT post_id, avatar_original_url
        FROM posts
        WHERE avatar_original_url IS NOT NULL AND avatar_original_url != ''
    """).fetchall()

    for post_id, avatar_original_url in avatar_rows:
        row = cur.execute("SELECT local_path FROM assets WHERE original_url=?", (avatar_original_url,)).fetchone()
        if row:
            cur.execute("UPDATE posts SET avatar_local_path=? WHERE post_id=?", (row[0], post_id))

    conn.commit()

    print("Assets téléchargés :", cur.execute("SELECT COUNT(*) FROM assets").fetchone()[0])
    print("Avatars liés :", cur.execute("SELECT COUNT(*) FROM posts WHERE avatar_local_path IS NOT NULL AND avatar_local_path != ''").fetchone()[0])

    conn.close()

if __name__ == "__main__":
    main()
