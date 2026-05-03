import os
import sys
import subprocess

STEPS = [
    "crawl.py",
    "download_assets.py",
    "build_site.py",
]

for step in STEPS:
    print("\n===", step, "===")
    subprocess.check_call([sys.executable, step])

print("\nTerminé.")
print("Mini-site :", os.path.abspath(os.path.join("jol_archive_output", "site", "index.html")))
print("DB finale :", os.path.abspath(os.path.join("jol_archive_output", "jol_archive.db")))
