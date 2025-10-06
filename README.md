# joss-repo-miner
Command-line tool to scrape accepted and published JOSS repositories into CSV.

python 3.9.6 was used to create this repository. So be mindful that (str | None (PEP 604) isn’t supported)

Usage:

```
python3 -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt

```

To run quick smoke test to check if it runs or not. (first 2 index pages) you can change the index number as you wish

```
 pip install -e .    
joss-repo-miner --status published --max-pages-published 2 --out results/published_sample.csv
```

To run it on all pages (all issues) use the following command 
```
joss-repo-miner --status accepted published --out results/joss_all.csv
```


Project Structure:

```
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

```

requirements.txt is generated using pipreqs. 

