# SK hynix DART Financial Dashboard

[![🔗 대시보드 바로가기](docs/dashboard-badge.svg)](https://HSC-Class01.github.io/HW_SKhynix/)

DART/OpenDART 기반으로 **SK hynix(000660)**의 사업보고서·반기보고서·분기보고서 재무 데이터를 수집하고, 주요 재무수치와 재무비율을 계산하여 GitHub Pages 대시보드로 제공합니다.

> **Dashboard:** https://HSC-Class01.github.io/HW_SKhynix/

## 1. 포함 지표

첨부된 「재무제표 및 재무비율 실무 가이드」의 핵심 항목을 기준으로 설계했습니다. 금액과 비율을 함께 보고, 최소 3~5개 기간의 추세를 비교하며, 연결/별도 기준을 섞지 않는다는 원칙을 반영합니다.

### 주요 재무수치
- 재무상태표: 총자산, 현금및현금성자산, 매출채권, 재고자산, 유형자산, 총부채, 이자부차입금, 자본총계
- 손익계산서: 매출액, 매출총이익, 판매비와관리비, 영업이익, 세전이익, 당기순이익, 지배주주순이익
- 현금흐름표: 영업활동현금흐름(CFO), 투자활동현금흐름, 재무활동현금흐름, CAPEX, FCF, 순차입금 관련 보조수치
- 재무비율: 매출총이익률, 영업이익률, 순이익률, ROA, ROE, ROIC(필요 조정값 확보 시), 유동비율, 당좌비율, 부채비율, 자기자본비율, 차입금의존도, 이자보상배율, 순차입금/EBITDA, 총자산회전율, DSO, DIO, DPO, CCC, 매출증가율, CFO/순이익, PER/PBR/EV/EBITDA

현재 구현은 OpenDART에서 안정적으로 확보되는 계정부터 자동 산출하고, 데이터가 없는 지표는 억지로 추정하지 않고 빈 값으로 둡니다.

## 2. 데이터 범위와 2010년 주의사항

OpenDART의 단일회사 전체 재무제표 API는 개발가이드상 **2015년 이후** 재무정보를 제공합니다. 따라서 2010~2014년은 OpenDART 재무 API만으로 자동 복원할 수 없습니다. 이 프로젝트는 `data/manual/legacy_2010_2014.csv`를 별도 경로로 두어 DART 원문에서 검증한 과거 수치를 넣을 수 있게 했습니다. 2010년 값은 부트스트랩 예시로 제공하며, 실제 제출용 데이터셋에서는 해당 연도 DART 사업보고서와 대조하여 확정하세요.

## 3. OpenDART API 키 설정

1. OpenDART에서 인증키를 발급합니다.
2. GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**
3. 이름: `DART_API_KEY`
4. 값: 발급받은 40자리 인증키
5. 절대로 API 키를 `README.md`, Python 코드, CSV, commit에 직접 입력하지 않습니다.

로컬 테스트:

```bash
pip install -r requirements.txt
export DART_API_KEY='발급받은_40자리_키'
python src/update_data.py
```

Windows PowerShell:

```powershell
$env:DART_API_KEY='발급받은_40자리_키'
python src/update_data.py
```

## 4. 자동 업데이트

`.github/workflows/update-and-deploy.yml`에서 매월 1일 **00:20 UTC(한국시간 09:20)**에 실행됩니다. 또한 `workflow_dispatch`로 수동 실행할 수 있고, 코드 변경 시에도 실행됩니다.

워크플로우는 다음 순서입니다.

1. GitHub Actions에서 Python 3.12 실행
2. OpenDART API 호출
3. 원본 JSON을 `data/raw/`에 저장
4. `data/financials.csv` 갱신
5. 변경된 데이터 commit
6. GitHub Pages artifact 생성
7. GitHub Pages 배포

## 5. GitHub Pages 설정

저장소 **Settings → Pages → Build and deployment → Source: GitHub Actions**로 한 번만 설정합니다. 이후 workflow가 배포를 담당합니다.

## 6. About 링크

저장소 메인 화면의 **About → 톱니바퀴(Edit repository details)**에서 Website에 아래 주소를 넣으세요.

`https://HSC-Class01.github.io/HW_SKhynix/`

이 설정은 저장소 메타데이터이므로 README 파일만으로는 변경되지 않습니다.

## 7. 국내 Peer Firms

직접 비교 가능성은 사업구조와 공시범위에 따라 달라지므로 '동일 업종 후보'로 구분합니다.

| 기업 | 종목코드 | 비교 맥락 |
|---|---:|---|
| 삼성전자 | 005930 | 메모리·시스템 반도체 및 전자 사업 |
| 한미반도체 | 042700 | HBM/반도체 후공정 장비 |
| 원익IPS | 240810 | 반도체 제조장비 |
| DB하이텍 | 000990 | 파운드리·반도체 설계 |
| 주성엔지니어링 | 036930 | 반도체·디스플레이 증착 장비 |

## 8. 파일 구조

```text
.
├── .github/workflows/update-and-deploy.yml
├── data/
│   ├── financials.csv
│   ├── status.json
│   ├── manual/legacy_2010_2014.csv
│   └── raw/                 # Actions 실행 시 생성
├── docs/dashboard-badge.svg
├── src/update_data.py
├── index.html
├── requirements.txt
├── .env.example
└── README.md
```

## 9. 데이터 해석 원칙

첨부 가이드의 원칙에 따라 금액과 비율을 함께 보고, 추세와 동종기업을 비교하며, 평균 자산/평균 자본을 사용하는 ROA·ROE 등은 가능한 경우 평균 잔액을 사용합니다. 일회성 항목과 연결/별도 기준도 구분합니다.

이 대시보드는 재무 데이터의 자동 수집·정리·시각화를 위한 분석 도구이며 투자 판단을 대신하지 않습니다.
