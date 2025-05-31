import json
from datetime import datetime
import requests as r
from bs4 import BeautifulSoup as bs


index_url = "https://www.mdcalc.com/_next/data/mbFTGi54cglQw_5xbY1ey/index.json"

def fetch_index():
    print(f"Fetching index from {index_url} at {datetime.now()}")
    response = r.get(index_url)
    
    if response.status_code != 200:
        print(f"Error fetching index: {response.status_code}")
        return None
    else:
        print(response.headers)
        return response.json()

def extract_text(html):
    soup = bs(html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def fetch_single_calculator(id,slug):
    item_url = f"https://www.mdcalc.com/_next/data/mbFTGi54cglQw_5xbY1ey/calc/{str(id)}/{slug}.json?slug={id}&slug={slug}"
    response = r.get(item_url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_by_path(data, path):
    try:
        for p in path:
            data = data[p]
        return data
    except (KeyError, TypeError):
        return None
def clean_single_calculator(data):
    key_map = {
        "title": (["pageProps", "headConfig", "title"], None),
        "full_title": (["pageProps", "calc", "full_title_en"], None),
        "short_title": (["pageProps", "calc", "short_title_en"], None),
        "med_description": (["pageProps", "calc", "medium_description_en"], extract_text),
        "short_description": (["pageProps", "calc", "short_description_en"], extract_text),
        "slug": (["pageProps", "calc", "slug"], None),
        "description": (["pageProps", "headConfig", "description"], None),
        "keywords": (["pageProps", "headConfig", "keywords"], None),
        "complaint": (["pageProps", "calc", "chief_complaint_en"], None),
        "formula": (["pageProps", "calc", "content", "about", "formula_en"], extract_text),
        "evidence": (["pageProps", "calc", "content", "about", "evidence_based_medicine_en"], None),
        "measurements": (["pageProps", "measurements"], None),
        "information": (["pageProps", "calc", "content", "about", "more_info_en"], None),
        "refrences": (["pageProps", "calc", "content", "about", "references_list"], None),
        "pearls": (["pageProps", "calc", "content", "how_to_use", "pearls_pitfalls_en"], None),
        "usecase": (["pageProps", "calc", "content", "how_to_use", "use_case_en"], None),
        "reasons": (["pageProps", "calc", "content", "how_to_use", "why_use_en"], None),
        "next_advice": (["pageProps", "calc", "content", "next_steps", "advice_en"], None),
        "next_actions": (["pageProps", "calc", "content", "next_steps", "critical_actions_en"], None),
        "next_management": (["pageProps", "calc", "content", "next_steps", "management_en"], None),
        "diseases": (["pageProps", "calc", "disease_en"], None),
        "input_schema": (["pageProps", "calc", "input_schema"], None),
        "instructions": (["pageProps", "calc", "instructions_en"], None),
        "published": (["pageProps", "calc", "publishedAt"], None),
        "purpose": (["pageProps", "calc", "purpose_en"], None),
        "search_terms": (["pageProps", "calc", "search_abbreviation_en"], None),
        "seo": (["pageProps", "calc", "seo"], None),
        "specialty": (["pageProps", "calc", "specialty_en"], None),
        "departments": (["pageProps", "calc", "system_en"], None),
        "tags": (["pageProps", "calc", "tags"], lambda x: x if x is not None else []),
        "version_number": (["pageProps", "calc", "versionNumber"], None),
        "versions": (["pageProps", "calc", "versions"], lambda x: x if x is not None else []),
        "related": (["pageProps", "relCalcs"], lambda x: x if x is not None else []),
        "ismed": (["pageProps", "isCMECalc"], lambda x: x if x is not None else False),
        "section": (["pageProps", "validSections"], lambda x: x if x is not None else []),
    }
    inter = {}
    for key, (path, func) in key_map.items():
        value = get_by_path(data, path)
        if func and value is not None:
            value = func(value)
        inter[key] = value
    print(len(inter.keys()))
    return inter