import requests
import pandas as pd
import re
from pathlib import Path
from Bio import Entrez
import yfinance as yf
import feedparser

# ⚠️ 반드시 자신의 이메일로 변경
Entrez.email = "iamcoolkorean@gmail.com"

def slugify(name: str) -> str:
    """약물명을 파일/폴더명에 안전한 형태로 변환"""
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')

def get_data_dir(drug_name: str) -> Path:
    """약물별 데이터 저장 폴더를 생성하고 경로 반환"""
    path = Path("data") / slugify(drug_name)
    path.mkdir(parents=True, exist_ok=True)
    return path

def fetch_clinical_trials(drug_name: str, condition: str = "", max_trials: int = 20) -> pd.DataFrame:
    """ClinicalTrials.gov에서 임상시험 정보 수집"""
    query = drug_name
    if condition:
        query += f" AND {condition}"

    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {"query.term": query, "pageSize": max_trials, "format": "json"}
    resp = requests.get(url, params=params)
    data = resp.json()

    studies = []
    for study in data.get("studies", []):
        prot = study["protocolSection"]
        ident = prot["identificationModule"]
        status = prot["statusModule"]
        design = prot.get("designModule", {})
        conditions = prot.get("conditionsModule", {}).get("conditions", [])

        studies.append({
            "nct_id": ident["nctId"],
            "title": ident.get("briefTitle", ""),
            "status": status.get("overallStatus", ""),
            "phases": ", ".join(design.get("phases", [])),
            "conditions": ", ".join(conditions),
        })

    df = pd.DataFrame(studies)
    save_path = get_data_dir(drug_name) / "clinical_trials.csv"
    df.to_csv(save_path, index=False)
    print(f"  → 임상시험 {len(df)}건 저장됨: {save_path}")
    return df

def fetch_pubmed(drug_name: str, extra_terms: str = "", max_results: int = 30) -> pd.DataFrame:
    """PubMed에서 논문 제목과 초록 수집"""
    query = f'"{drug_name}" {extra_terms}'.strip()
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()

    ids = record.get("IdList", [])
    if not ids:
        print("  → PubMed 검색 결과 없음")
        return pd.DataFrame()

    handle = Entrez.efetch(db="pubmed", id=ids, rettype="xml", retmode="xml")
    papers = Entrez.read(handle)
    handle.close()

    articles = []
    for paper in papers.get("PubmedArticle", []):
        article = paper["MedlineCitation"]["Article"]
        abstract_list = article.get("Abstract", {}).get("AbstractText", [""])
        abstract = " ".join(abstract_list) if isinstance(abstract_list, list) else str(abstract_list)
        articles.append({
            "pmid": paper["MedlineCitation"]["PMID"],
            "title": article.get("ArticleTitle", ""),
            "abstract": abstract,
        })

    df = pd.DataFrame(articles)
    save_path = get_data_dir(drug_name) / "pubmed.csv"
    df.to_csv(save_path, index=False)
    print(f"  → PubMed 논문 {len(df)}건 저장됨: {save_path}")
    return df

def fetch_news(drug_name: str, competitors: list = None) -> pd.DataFrame:
    """RSS 피드에서 관련 뉴스 헤드라인 수집"""
    keywords = [drug_name.lower()]
    if competitors:
        keywords.extend([c.lower() for c in competitors])

    feeds = [
        "https://feeds.fiercepharma.com/FiercePharma",
        "https://www.fiercebiotech.com/feed/",
    ]

    articles = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:
            if any(kw in entry.title.lower() for kw in keywords):
                articles.append({
                    "source": feed.feed.get("title", ""),
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", ""),
                })

    df = pd.DataFrame(articles)
    if not df.empty:
        save_path = get_data_dir(drug_name) / "news.csv"
        df.to_csv(save_path, index=False)
        print(f"  → 뉴스 {len(df)}건 저장됨: {save_path}")
    else:
        print("  → 관련 뉴스 없음")
    return df

def fetch_financials(drug_name: str, ticker_dict: dict) -> pd.DataFrame:
    """Yahoo Finance에서 회사 재무 정보 수집"""
    rows = []
    for ticker, name in ticker_dict.items():
        stock = yf.Ticker(ticker)
        info = stock.info
        rows.append({
            "company": name,
            "ticker": ticker,
            "marketCap": info.get("marketCap"),
            "enterpriseValue": info.get("enterpriseValue"),
            "totalRevenue": info.get("totalRevenue"),
            "netIncome": info.get("netIncomeToCommon"),
            "trailingPE": info.get("trailingPE"),
        })

    df = pd.DataFrame(rows)
    save_path = get_data_dir(drug_name) / "financials.csv"
    df.to_csv(save_path, index=False)
    print(f"  → 재무정보 {len(df)}건 저장됨: {save_path}")
    return df
