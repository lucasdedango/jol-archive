# JOL Archive Tool — version multi-process safe

## Installation

Dans PowerShell :

```powershell
cd C:\Users\lucasdedango-fix\Documents\jol_archive_tool
py -m pip install -r requirements.txt
```

## Lancement

```powershell
py run_all.py
```

## Résultat

Mini-site :

```text
jol_archive_output\site\index.html
```

Base SQLite :

```text
jol_archive_output\jol_archive.db
```

## Réglages importants

Dans `config.py` :

```python
FORUM_PAGE_START = 1
FORUM_PAGE_END = 2350

CRAWL_PROCESSES = 4
HTML_WORKERS_PER_PROCESS = 4
ASSET_WORKERS = 24
```

Avec un i9 14900, tu peux tester :

```python
CRAWL_PROCESSES = 5
HTML_WORKERS_PER_PROCESS = 4
ASSET_WORKERS = 32
```

Évite de monter trop haut : le serveur distant peut ralentir ou refuser.

## Reprise après crash/interruption

Par défaut :

```python
RESET_BEFORE_CRAWL = False
```

Donc tu relances simplement :

```powershell
py run_all.py
```

Chaque worker possède sa propre base SQLite dans :

```text
jol_archive_output\workers\
```

Puis les DB sont fusionnées à la fin.

## Filtre par date du premier post

Dans `config.py` :

```python
FIRST_POST_DATE_START = "01/01/2004"
FIRST_POST_DATE_END = "01/01/2005"
```

Ou `None` pour désactiver.
