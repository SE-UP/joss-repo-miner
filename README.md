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

Before running the scripts to get all published repositories make sure you have your github token in .env How to do it. 


To run it on all pages (all issues) use the following command 
```
joss-repo-miner --status accepted published --out results/joss_all.csv
```


Project Structure:

```
joss-repo-miner/
├─ .env
├─ requirements.txt
├─ tests/
│  └─ unit/
│     ├─ utils/
│        ├─ test_http.py
│        └─ test_io.py
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





To be included in github tokens

### Generate and use a GitHub token (classic)

**1) Create a new token (classic)**  
GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → **Generate new token (classic)**  
*(No scopes needed for public data; optionally add `public_repo`.)*

**2) Save to `.env` (no quotes, no spaces)**  
    GITHUB_TOKEN=YOUR_TOKEN_HERE
    GITHUB_USERNAME=YourGitHubUser

**3) Load and verify in your shell**  
    set -a
    source .env
    set +a

    # sanity-check it loaded
    echo ${#GITHUB_TOKEN}               # should be > 0
    echo "${GITHUB_TOKEN:0:6}******"

    # test both header styles
    curl -sH "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit | head
    curl -sH "Authorization: token $GITHUB_TOKEN"  https://api.github.com/rate_limit | head
