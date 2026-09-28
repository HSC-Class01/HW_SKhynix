# SK hynix DART Financial Dashboard

[![🔗 대시보드 바로가기](https://img.shields.io/badge/🔗-대시보드%20바로가기-2563eb?style=for-the-badge)](https://HSC-Class01.github.io/HW_SKhynix/)

DART Open API 기반으로 SK hynix(000660)의 사업보고서·반기보고서·분기보고서 재무 데이터를 수집하고, 연간/반기/분기 테이블 및 재무비율 대시보드를 생성합니다.

## 시작하기
1. 저장소 루트에 이 프로젝트 파일을 업로드합니다.
2. GitHub 저장소 **Settings → Secrets and variables → Actions → New repository secret**에서 `DART_API_KEY`를 만들고 OpenDART 인증키를 입력합니다.
3. **Settings → Pages**에서 Build and deployment를 `Deploy from a branch`, Branch `main`, Folder `/ (root)`로 설정합니다.
4. Actions에서 `DART financial data update`를 수동 실행해 초기 수집을 확인합니다. 이후 매월 1일 UTC 00:20(한국시간 09:20)에 자동 실행됩니다.
5. 저장소의 About(톱니바퀴)에서 Website에 `https://HSC-Class01.github.io/HW_SKhynix/`를 입력합니다.

## 수집 범위와 지표
2010년부터 OpenDART 정기보고서 목록을 조회하고 사업/반기/분기 보고서의 재무제표(XBRL)를 가져옵니다. 보고서에 존재하는 매출액, 영업이익, 당기순이익, 자산총계, 부채총계, 자본총계, 현금및현금성자산, 영업활동현금흐름을 우선 추출합니다. ROE, ROA, 부채비율, 영업이익률, 순이익률은 사용 가능한 값으로 계산합니다. 원본 API 응답과 정규화 데이터는 `data/`에 저장됩니다.

> 주의: OpenDART가 제공하는 계정명/표시 방식 및 보고서별 비교기간 차이로 일부 항목은 비어 있을 수 있습니다. 분석 참고용이며 투자 판단을 대신하지 않습니다.

## 국내 peer firms
아래 기업은 국내 반도체 업종 비교 후보입니다. 사업 구조와 공시 가능 범위가 달라 직접 비교 시 유의하세요.

| 기업 | 종목코드 | 비교 맥락 |
|---|---:|---|
| 삼성전자 | 005930 | 메모리·시스템 반도체 및 전자 사업 |
| 한미반도체 | 042700 | 반도체 후공정 장비 |
| 리노공업 | 058470 | 반도체 검사 부품·소켓 |
| 원익IPS | 240810 | 반도체·디스플레이 제조장비 |
| DB하이텍 | 000990 | 파운드리·반도체 설계 |

## 로컬 실행
```bash
pip install -r requirements.txt
export DART_API_KEY="발급받은_인증키"
python src/update_data.py
```
