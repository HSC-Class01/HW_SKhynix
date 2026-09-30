# SK hynix DART Financial Dashboard

[![🔗 대시보드 바로가기](dashboard-badge.svg)](https://HSC-Class01.github.io/HW_SKhynix/)

**[🔗 대시보드 바로가기](https://HSC-Class01.github.io/HW_SKhynix/)**

DART/OpenDART를 이용해 **SK hynix (000660)**의 사업보고서·반기보고서·분기보고서를 수집하고, 연결재무제표를 우선 기준으로 주요 재무수치와 재무비율을 산출하는 GitHub 기반 agent입니다.

## 구현 범위
- OpenDART API 기반 정기보고서 재무정보 수집
- 사업보고서(Annual), 반기보고서(Half-year), 분기보고서(Quarterly) 분리
- 누적 분기공시를 이용해 Q1/Q2/Q3/Q4 standalone 산출
- 주요 재무수치와 수익성·유동성·레버리지·효율성 비율 계산
- GitHub Actions 매월 1일 자동 실행 및 GitHub Pages 자동 배포
- 상단 KPI/그래프 + Annual/Half-year/Quarterly 전체 표
- 국내 Peer Firms 표
- 우측 floating PDF/Excel 다운로드 패널

## 2010년 데이터
OpenDART의 구조화된 단일회사 주요계정/전체 재무제표 API는 **2015년 이후 사업연도**부터 정보를 제공합니다. 따라서 2010~2014년을 같은 API endpoint로 자동 복원할 수 없습니다. 이 저장소는 임의 추정 대신 `data/manual/legacy_2010_2014.csv`를 별도 레이어로 두었습니다.

2010~2014년 DART 원문을 검증한 뒤 동일한 컬럼 구조로 입력하면 agent가 자동 통합합니다. 레거시 값은 `DART legacy/manual`로 표시합니다. DART는 공시 원문 XML과 XBRL 원본 파일도 별도로 제공합니다.

## API Key
1. [OpenDART](https://opendart.fss.or.kr/)에서 인증키 발급
2. GitHub → **Settings → Secrets and variables → Actions**
3. **New repository secret**
4. Name: `DART_API_KEY`
5. 발급받은 40자리 키 입력

**API Key를 코드/README/CSV/commit에 직접 입력하지 마세요.**

로컬:
```bash
export DART_API_KEY='발급받은_40자리_키'
pip install -r requirements.txt
python update_data.py
```

Windows PowerShell:
```powershell
$env:DART_API_KEY='발급받은_40자리_키'
pip install -r requirements.txt
python update_data.py
```

## 자동 업데이트
`.github/workflows/main.yml`은 **매월 1일 09:20 KST (00:20 UTC)**에 실행됩니다. `workflow_dispatch` 수동 실행도 지원하며 코드 변경 시에도 실행됩니다.

순서: DART 수집 → raw JSON 저장 → normalized CSV/ratios 생성 → 변경 데이터 commit → GitHub Pages 배포.

## GitHub Pages
**Settings → Pages → Build and deployment → Source: GitHub Actions**를 확인합니다.

배포 주소:
**https://HSC-Class01.github.io/HW_SKhynix/**

## About 링크
GitHub 저장소의 오른쪽 **About → Edit repository details → Website**에 다음을 입력하세요.

`https://HSC-Class01.github.io/HW_SKhynix/`

현재 연결된 GitHub 도구에는 repository metadata의 homepage 필드를 직접 수정하는 기능이 노출되어 있지 않아 이 항목은 GitHub 화면에서 한 번 설정해야 합니다.

## 국내 Peer Firms
| 기업 | 종목코드 | 비교 맥락 |
|---|---:|---|
| 삼성전자 | 005930 | 메모리·시스템 반도체 및 전자 사업 |
| 한미반도체 | 042700 | HBM/반도체 후공정 장비 |
| DB하이텍 | 000990 | 파운드리 중심 반도체 제조 |
| 원익IPS | 240810 | 반도체·디스플레이 제조장비 |
| 주성엔지니어링 | 036930 | 반도체·디스플레이 증착 장비 |

## 다운로드
- **PDF**: 현재 대시보드 화면을 PDF로 저장
- **Excel**: Annual / Half-year / Quarterly 선택 후 해당 기간 데이터 다운로드

## 구조
```text
HW_SKhynix/
├── .github/workflows/main.yml
├── data/financials.csv
├── data/status.json
├── data/raw/
├── data/manual/legacy_2010_2014.csv
├── index.html
├── update_data.py
├── requirements.txt
└── README.md
```

## 비율 정의
- Gross margin = Gross profit / Revenue
- Operating margin = Operating income / Revenue
- Net margin = Net income / Revenue
- ROA = Net income / Average total assets
- ROE = Net income / Average total equity
- Current ratio = Current assets / Current liabilities
- Debt ratio = Total liabilities / Total equity
- Equity ratio = Total equity / Total assets
- Net debt = Interest-bearing debt − Cash
- FCF = CFO − |CAPEX|
- Interest coverage = Operating income / |Interest expense|
- Asset turnover = Revenue / Total assets

OpenDART 원문과 대조하여 연구·분석에 사용하시기 바랍니다. 이 저장소는 투자판단을 대신하지 않습니다.
