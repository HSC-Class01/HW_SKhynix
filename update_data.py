import os, io, json, time, zipfile
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
RAW = DATA / 'raw'
MANUAL = DATA / 'manual'
RAW.mkdir(parents=True, exist_ok=True)
MANUAL.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv('DART_API_KEY', '').strip()
CORP_CODE = os.getenv('DART_CORP_CODE', '00164779').strip()  # SK hynix corp code
STOCK_CODE = '000660'
START_YEAR = 2015  # OpenDART financial APIs document coverage from 2015 onward.
END_YEAR = datetime.now().year
REPORTS = {'11011':'annual','11012':'half','11013':'quarterly','11014':'quarterly'}
REPORT_NAMES = {'11011':'사업보고서','11012':'반기보고서','11013':'1분기보고서','11014':'3분기보고서'}
BASE = 'https://opendart.fss.or.kr/api'

# User guide requested these core figures. Account matching accepts common Korean/XBRL labels.
ACCOUNTS = {
    'total_assets':['자산총계','Assets'],
    'current_assets':['유동자산','Current assets'],
    'current_liabilities':['유동부채','Current liabilities'],
    'cash':['현금및현금성자산','현금및현금성자산(현금및현금성자산)'],
    'receivables':['매출채권','매출채권 및 기타채권','Trade receivables'],
    'inventory':['재고자산','Inventories'],
    'ppe':['유형자산','Property, plant and equipment'],
    'total_liabilities':['부채총계','Liabilities'],
    'interest_bearing_debt':['이자부차입금','차입금','Borrowings'],
    'total_equity':['자본총계','자본','Equity'],
    'revenue':['매출액','수익(매출액)','Revenue'],
    'gross_profit':['매출총이익','Gross profit'],
    'sga':['판매비와관리비','Selling and administrative expenses'],
    'operating_income':['영업이익','영업이익(손실)','Operating income'],
    'pretax_income':['법인세비용차감전순이익','세전이익','Profit before tax'],
    'net_income':['당기순이익','연결총당기순이익','Profit for the period'],
    'net_income_parent':['지배기업의 소유주에게 귀속되는 당기순이익','지배기업의 소유주지분','Profit attributable to owners'],
    'cfo':['영업활동현금흐름','영업활동으로 인한 현금흐름','Net cash flows from operating activities'],
    'cfi':['투자활동현금흐름','투자활동으로 인한 현금흐름','Net cash flows from investing activities'],
    'cff':['재무활동현금흐름','재무활동으로 인한 현금흐름','Net cash flows from financing activities'],
    'capex':['유형자산의 취득','유형자산 취득','Purchase of property, plant and equipment'],
    'interest_expense':['이자비용','금융비용','Interest expense'],
}

def num(v):
    if v is None or str(v).strip() in ('','-','–','—','N/A'):
        return None
    s = str(v).replace(',','').replace(' ','').replace('(','-').replace(')','')
    try: return float(s)
    except: return None

def api_get(path, params):
    params = dict(params); params['crtfc_key'] = API_KEY
    r = requests.get(f'{BASE}/{path}.json', params=params, timeout=60)
    r.raise_for_status()
    obj = r.json()
    if obj.get('status') != '000':
        raise RuntimeError(f"DART {path}: {obj.get('status')} {obj.get('message')}")
    return obj

def corp_name_from_code():
    return 'SK hynix'

def match_account(name, aliases):
    n = str(name).strip().lower()
    return any(a.lower() in n or n in a.lower() for a in aliases)

def extract(rows, key):
    aliases = ACCOUNTS[key]
    # Prefer CFS rows with the exact account and the current period amount.
    cand = [r for r in rows if match_account(r.get('account_nm'), aliases)]
    if not cand: return None
    # Prefer the first row with an amount; OpenDART usually orders the canonical row first.
    for r in cand:
        for fld in ('thstrm_amount','thstrm_add_amount'):
            v = num(r.get(fld))
            if v is not None: return v
    return None

def period_end(year, report):
    return { '11011':f'{year}-12-31', '11012':f'{year}-06-30', '11013':f'{year}-03-31', '11014':f'{year}-09-30' }[report]

def fetch_year(year, report):
    # OpenDART financial endpoint: documented from 2015 onward.
    obj = api_get('fnlttSinglAcntAll', {'corp_code':CORP_CODE,'bsns_year':str(year),'reprt_code':report,'fs_div':'CFS'})
    (RAW / f'{year}_{report}.json').write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = obj.get('list', [])
    if not rows: return None
    out = {'fiscal_year':year,'period_end':period_end(year,report),'period_type':REPORTS[report],'report_code':report,'report_name':REPORT_NAMES[report],'corp_code':CORP_CODE,'stock_code':STOCK_CODE,'currency_unit':None}
    # Use all account values from the response.
    for key in ACCOUNTS:
        out[key] = extract(rows, key)
    # Carry unit from any row.
    out['currency_unit'] = next((r.get('currency') for r in rows if r.get('currency')), None)
    # Source metadata
    out['rcept_no'] = next((r.get('rcept_no') for r in rows if r.get('rcept_no')), '')
    out['dart_url'] = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={out['rcept_no']}" if out['rcept_no'] else ''
    return out

def add_derived(df):
    df = df.copy()
    for c in ['revenue','gross_profit','operating_income','net_income','total_assets','total_liabilities','total_equity','cash','cfo','capex','interest_expense','interest_bearing_debt']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    # DART returns statement amounts in the report's stated unit; dashboard converts to trillion KRW.
    # For ratios, use average beginning/end balances where available.
    df = df.sort_values(['period_type','period_end'])
    df['operating_margin'] = df['operating_income'] / df['revenue']
    df['net_margin'] = df['net_income'] / df['revenue']
    df['gross_margin'] = df['gross_profit'] / df['revenue']
    df['debt_ratio'] = df['total_liabilities'] / df['total_equity']
    df['equity_ratio'] = df['total_equity'] / df['total_assets']
    df['current_ratio'] = df.get('current_assets', pd.Series(index=df.index, dtype=float)) / df.get('current_liabilities', pd.Series(index=df.index, dtype=float))
    # FCF uses CFO - cash CAPEX per the supplied guide.
    df['fcf'] = df['cfo'] - df['capex'].abs()
    df['cfo_to_net_income'] = df['cfo'] / df['net_income']
    # Growth is meaningful only within annual series; compare same report type for quarter/half.
    df['revenue_growth'] = df.groupby('period_type')['revenue'].pct_change()
    # Average balance ratios: align previous period of same type.
    for base in ['total_assets','total_equity']:
        prev = df.groupby('period_type')[base].shift(1)
        avg = (df[base] + prev) / 2
        if base == 'total_assets': df['roa'] = df['net_income'] / avg
        else: df['roe'] = df['net_income'] / avg
    return df

def collect_report_index():
    rows=[]
    for year in range(START_YEAR, END_YEAR+1):
        try:
            obj=api_get('list', {'corp_code':CORP_CODE,'bgn_de':f'{year}0101','end_de':f'{year}1231','page_no':'1','page_count':'100'})
            for r in obj.get('list',[]):
                nm=r.get('report_nm','')
                if any(k in nm for k in ('사업보고서','반기보고서','분기보고서')):
                    rows.append({'fiscal_year':year,'report_name':nm,'report_date':r.get('rcept_dt',''),'rcept_no':r.get('rcept_no',''),'reporter':r.get('corp_name',''),'dart_url':f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r.get('rcept_no','')}"})
        except Exception as e:
            print(f'[WARN] report index {year}: {e}')
        time.sleep(0.12)
    if rows:
        pd.DataFrame(rows).drop_duplicates('rcept_no').sort_values('report_date').to_csv(DATA/'reports.csv',index=False,encoding='utf-8-sig')

def main():
    if not API_KEY:
        raise SystemExit('DART_API_KEY is required. Add it as a GitHub Actions repository secret or environment variable.')
    rows=[]
    for year in range(START_YEAR, END_YEAR+1):
        for report in REPORTS:
            try:
                item = fetch_year(year, report)
                if item: rows.append(item)
                time.sleep(0.12)
            except Exception as e:
                print(f'[WARN] {year} {report}: {e}')
    collect_report_index()
    # Preserve user-provided/manual legacy observations if present.
    legacy = MANUAL / 'legacy_2010_2014.csv'
    if legacy.exists() and legacy.stat().st_size:
        leg = pd.read_csv(legacy, comment='#')
    else:
        leg = pd.DataFrame()
    fresh = pd.DataFrame(rows)
    if not fresh.empty and not leg.empty:
        all_df = pd.concat([leg, fresh], ignore_index=True, sort=False)
    else:
        all_df = fresh if not fresh.empty else leg
    if all_df.empty:
        raise SystemExit('No financial rows were returned.')
    all_df = add_derived(all_df)
    all_df = all_df.drop_duplicates(subset=['fiscal_year','period_type','period_end'], keep='last').sort_values(['period_end','period_type'])
    all_df.to_csv(DATA / 'financials.csv', index=False, encoding='utf-8-sig')
    summary = {'updated_at_utc':datetime.utcnow().isoformat(timespec='seconds')+'Z','rows':len(all_df),'start_year':int(all_df.fiscal_year.min()),'latest_period':str(all_df.period_end.max())}
    (DATA / 'status.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == '__main__': main()
