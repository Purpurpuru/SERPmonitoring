"""streamlit_app.py
Interactive Streamlit front-end for serp_fetcher.py
---------------------------------------------------
Run with:
    streamlit run streamlit_app.py
"""
from __future__ import annotations
import io, time, os
from urllib.parse import urlparse
from typing import List, Dict

import pandas as pd
import streamlit as st
from dataforseo_client import configuration as dfs_config, api_client as dfs_provider
from dataforseo_client.api.serp_api import SerpApi
from dataforseo_client.models.serp_google_organic_live_advanced_request_info import SerpGoogleOrganicLiveAdvancedRequestInfo
from dataforseo_client.rest import ApiException

RATE_LIMIT_DELAY = 1.0
MAX_RETRIES = 5

st.set_page_config(page_title="SERP Fetcher", layout="wide")
st.title("DataforSEO SERP Fetcher – Streamlit Edition")

# Sidebar controls
location_code = st.sidebar.number_input("location_code", value=2840)
language_code = st.sidebar.text_input("language_code", value="en")
device = st.sidebar.selectbox("device", ["desktop", "mobile"], index=0)
depth = st.sidebar.slider("depth", 1, 100, 20)
people_also_ask_depth = st.sidebar.slider("people_also_ask_depth", 0, 6, 0)
group_organic = st.sidebar.checkbox("group_organic_results")
ai_overview = st.sidebar.checkbox("load_async_ai_overview")
se_domain = st.sidebar.text_input("se_domain", value="google.com")
target = st.sidebar.text_input("target (optional)")

keywords_text = st.text_area("Keywords (one per line)", "auto vin check\ncar history report\nvehicle mileage check")
keywords = [k.strip() for k in keywords_text.splitlines() if k.strip()]

def make_api():
    login=os.getenv("DFS_LOGIN"); password=os.getenv("DFS_PASSWORD")
    if not (login and password): st.error("Set DFS_LOGIN & DFS_PASSWORD"); st.stop()
    cfg=dfs_config.Configuration(username=login,password=password)
    return SerpApi(dfs_provider.ApiClient(cfg))

def build_task(kw:str)->SerpGoogleOrganicLiveAdvancedRequestInfo:
    t=SerpGoogleOrganicLiveAdvancedRequestInfo(keyword=kw, language_code=language_code, location_code=int(location_code), device=device, depth=int(depth), se_domain=se_domain)
    if people_also_ask_depth: t.people_also_ask_depth=int(people_also_ask_depth)
    if group_organic: t.group_organic_results=True
    if ai_overview: t.load_async_ai_overview=True
    if target: t.target=target
    return t

def parse_items(kw:str, items:List[Dict])->List[Dict]:
    rows=[]
    for itm in items:
        if itm.get("type")!="organic": continue
        rank=int(itm.get("rank_absolute",0))
        if rank==0 or rank>depth: continue
        url=itm.get("url","")
        rows.append({"keyword":kw,"rank":rank,"title":itm.get("title",""),"snippet":itm.get("description",""),"url":url,"is_autodna":"true" if "autodna" in urlparse(url).netloc.lower() else "false"})
    return rows

if st.button("Run Query"):
    if not keywords: st.warning("Enter keywords"); st.stop()
    api=make_api()
    rows=[]
    prog=st.progress(0.0)
    for idx,kw in enumerate(keywords,1):
        task=build_task(kw); delay=RATE_LIMIT_DELAY
        for att in range(1,MAX_RETRIES+1):
            try:
                res=api.google_organic_live_advanced([task])
                items=res.to_dict()["tasks"][0]["result"][0]["items"]
                rows.extend(parse_items(kw,items)); break
            except ApiException as e:
                if e.status in {429,500,502,503,504} and att<MAX_RETRIES:
                    time.sleep(delay); delay*=2
                else: st.error(f"API error on '{kw}': {e}"); break
        time.sleep(RATE_LIMIT_DELAY); prog.progress(idx/len(keywords))
    prog.empty()
    if rows:
        df=pd.DataFrame(rows).sort_values(["keyword","rank"])
        st.dataframe(df,use_container_width=True)
        csv=io.StringIO(); df.to_csv(csv,index=False)
        st.download_button("Download CSV", data=csv.getvalue(), file_name="serp_results.csv", mime="text/csv")
