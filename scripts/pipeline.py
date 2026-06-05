from scripts.data_loader import (
    fetch_clinical_trials,
    fetch_pubmed,
    fetch_news,
    fetch_financials,
    get_data_dir,
)

def run_pipeline(
    drug_name: str,
    condition: str = "",
    extra_pubmed: str = "",
    competitors: list = None,
    tickers: dict = None,
):
    """
    하나의 약물에 대해 데이터 수집 전체를 자동 실행
    """
    print(f"\n🔬 === From Molecule to Multiple | 데이터 수집 시작 === 🔬")
    print(f"🎯 대상 약물: {drug_name}")
    print(f"📁 저장 경로: {get_data_dir(drug_name)}\n")

    # 1. 임상시험
    print("1/4 ClinicalTrials.gov 수집 중...")
    try:
        fetch_clinical_trials(drug_name, condition)
    except Exception as e:
        print(f"  ❌ 임상시험 수집 실패: {e}")

    # 2. PubMed 논문
    print("2/4 PubMed 논문 수집 중...")
    try:
        fetch_pubmed(drug_name, extra_pubmed)
    except Exception as e:
        print(f"  ❌ PubMed 수집 실패: {e}")

    # 3. 뉴스
    print("3/4 뉴스 수집 중...")
    try:
        fetch_news(drug_name, competitors)
    except Exception as e:
        print(f"  ❌ 뉴스 수집 실패: {e}")

    # 4. 재무 정보 (옵션)
    if tickers:
        print("4/4 재무 정보 수집 중...")
        try:
            fetch_financials(drug_name, tickers)
        except Exception as e:
            print(f"  ❌ 재무정보 수집 실패: {e}")
    else:
        print("4/4 재무 정보는 생략 (tickers 미지정)")

    print(f"\n✅ 모든 데이터 수집 완료! → {get_data_dir(drug_name)}")
    print("=" * 50)
