# joss-repo-miner
Command-line tool to scrape accepted and published JOSS repositories into CSV.

python 3.9.6 was used to create this repository. 

Usage:

python3 -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt



joss-repo-miner/
├─ .env
├─ requirements.txt
├─ src/
│  └─ joss_repo_miner/
│     ├─ __init__.py
│     ├─ __main__.py
│     ├─ cli.py
│     ├─ config.py
│     ├─ utils/
│     │  ├─ __init__.py
│     │  ├─ http.py
│     │  ├─ io.py
│     │  └─ parsing.py
│     └─ scrapers/
│        ├─ __init__.py
│        ├─ accepted.py
│        └─ published.py
├─ results/
├─ LICENSE
└─ .gitignore




