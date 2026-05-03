JOL Archive Tool - version simple avec reprise fiable
====================================================

Cette version n'utilise plus de multi-process.
Elle écrit tout dans une seule base SQLite : jol_archive_output/jol_archive.db

Lancement Windows PowerShell :

cd C:\Users\lucasdedango-fix\Documents\jol_archive_tool
py -m pip install -r requirements.txt
py run_all.py

Reprise :
- Par défaut RESET_BEFORE_CRAWL = False dans config.py.
- Tu peux interrompre avec Ctrl+C.
- Relance py run_all.py : les pages forum, les pages topics et les assets déjà faits sont ignorés.

Recommencer de zéro :
- Mets RESET_BEFORE_CRAWL = True dans config.py, lance une fois, puis remets False.
- Ou supprime le dossier jol_archive_output.

Réglages utiles dans config.py :
- FORUM_PAGE_START / FORUM_PAGE_END : intervalle de pages forum.
- FIRST_POST_DATE_START / FIRST_POST_DATE_END : filtre sur la date du premier post.
- HTML_WORKERS : threads internes pour pages topics, conseillé 3 à 6.
- ASSET_WORKERS : threads pour images/avatars, conseillé 8 à 16.
- ASK_BIG_TOPICS / BIG_TOPIC_THRESHOLD : confirmation pour les gros topics.

Résultat :
- Mini-site : jol_archive_output/site/index.html
- Base : jol_archive_output/jol_archive.db
