# joss-repo-miner
Command-line tool to scrape published JOSS repositories into CSV.

* **Project Structure**

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

**Usage:**

* **[Step:1]** Creating a virtual environment. 

**1.1:** Create a .venv using following command.
```   
python3 -m venv venv
```   

 **1.2:** Activate it (macOS/Linux).
```   
source venv/bin/activate 
```   

**[At the end]** Deactivate it when done. 
``` 
deactivate
```   
* **[Step:2]** Installing dependencies

**2.1:** We used pipreqs to create requirements.txt file given this repository contains only the code 
You can install requirements.txt using the below 
```   
pip install -r requirements.txt
```   
* **[Step:3]** Install and run.

To run quick smoke test to check if it runs or not. (first 2 index pages) you can change the index number as you wish
```
 pip install -e .    
joss-repo-miner --status published --max-pages-published 2 --out results/published_sample.csv
```
Use the following command to make the full run: 
```
joss-repo-miner --status published --out results/joss_all.csv
```