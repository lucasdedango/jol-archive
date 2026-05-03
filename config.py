# =========================
# CONFIG ARCHIVE JOL
# =========================

BASE = "https://forums.jeuxonline.info"
FORUM_ID = 277
FORUM_SLUG = "dofus-le-village-des-tofus-perdus"

# Pages forum à scanner
FORUM_PAGE_START = 2000
FORUM_PAGE_END = 2350

# Filtre optionnel sur la date du PREMIER post du topic.
# Format "JJ/MM/AAAA" ou None.
FIRST_POST_DATE_START = None
FIRST_POST_DATE_END = None
# Exemple :
# FIRST_POST_DATE_START = "01/01/2004"
# FIRST_POST_DATE_END = "01/01/2005"

# Plus de multi-process : une seule base SQLite, reprise fiable.
# Threads internes raisonnables pour les pages topic.
HTML_WORKERS = 32

# Threads pour télécharger les images/avatars après crawl.
ASSET_WORKERS = 32

# Gros topics : demande confirmation si plus de X pages.
ASK_BIG_TOPICS = True
BIG_TOPIC_THRESHOLD = 30

# Si True, supprime l'ancienne sortie avant de recommencer de zéro.
# Si False, reprend automatiquement.
RESET_BEFORE_CRAWL = False

# Politesse réseau
WAIT_FORUM_PAGES = 0.1

# Dossier de sortie local
OUT = "jol_archive_output"

# User-Agent navigateur
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}
