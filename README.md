# SERP Fetcher & Streamlit App

## Overview
Python 3 toolkit for querying Google SERP data via DataforSEO v3 and presenting the results via command‑line or Streamlit.

### Components
| file | purpose |
|------|---------|
| `serp_fetcher.py` | CLI utility exporting CSV |
| `streamlit_app.py` | Streamlit UI, query & download |
| `requirements.txt` | dependencies |
| `keywords.txt` | sample keyword list |

## Quick Start
```bash
pip install -r requirements.txt
export DFS_LOGIN=your_login
export DFS_PASSWORD=your_password
python serp_fetcher.py keywords.txt results.csv
streamlit run streamlit_app.py
```
