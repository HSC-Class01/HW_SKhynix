import os, json, time
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT=Path(__file__).resolve().parent; DATA=ROOT/"data"; RAW=DATA/"raw"; MANUAL=DATA/"manual"
RAW.mkdir(parents=True,exist_ok=True); MANUAL.mkdir(parents=True,exist_ok=True)
API_KEY=os.getenv("DART_API_KEY","").strip(); CORP_CODE=os.getenv("DART_CORP_CODE","00164779").strip()
STOCK_CODE="000660"; START_YEAR=int(os.getenv("START_YEAR","2015")); END_YEAR=datetime.now().year
BASE="https://opendart.fss.or.kr/api"
REPORTS={"11011":"annual","11012":"half","11013":"quarterly","11014":"quarterly"}
REPORT_NAMES={"11011":"사업보고서","11012":"반기보고서","11013":"1분기보고서","11014":"3분기보고서"}
ACCOUNTS={
"total_assets":["자산총계","Assets"],"current_assets":["유동자산","Current assets"],
"current_liabilities":["유동부채","Current liabilities"],"cash":["현금및현금성자산","Cash and cash equivalents"],
"receivables":["매출채권","매출채권 및 기타채권","Trade receivables"],"inventory":["재고자산","Inventories"],
"ppe":["유형자산","Property, plant and equipment"],"total_liabilities":["부채총계","Liabilities"],
"interest_bearing_debt":["차입금","사채","Borrowings"],"total_equity":["자본총계","자본","Equity"],
"revenue":["매출액","수익(매출액)","Revenue"],"gross_profit":["매출총이익","Gross profit"],
"sga":["판매비와관리비","Selling and administrative expenses"],"operating_income":["영업이익","영업이익(손실)","Operating income"],
"pretax_income":["법인세비용차감전순이익","세전이익","Profit before tax"],
"net_income":["당기순이익","연결총당기순이익","Profit for the period"],
"net_income_parent":["지배기업의 소유주에게 귀속되는 당기순이익","지배기업의 소유주지분","Profit attributable to owners"],
"cfo":["영업활동현금흐름","영업활동으로 인한 현금흐름","Net cash flows from operating activities"],
"cfi":["투자활동현금흐름","투자활동으로 인한 현금흐름","Net cash flows from investing activities"],
"cff":["재무활동현금흐름","재무활동으로 인한 현금흐름","Net cash flows from financing activities"],
"capex":["유형자산의 취득","유형자산 취득","Purchase of property, plant and equipment"],
"interest_expense":["이자비용","금융비용","Interest expense"]}

def num(v):
    if v is None or str(v).strip() in ("","-","–","—","N/A"): return None
    try: return float(str(v).replace(",","").replace(" ","").replace("(","-").replace(")",""))
    except (ValueError,TypeError): return None

def api_get(path,params):
    p=dict(params); p["crtfc_key"]=API_KEY
    r=requests.get(f"{BASE}/{path}.json",params=p,timeout=60); r.raise_for_status(); obj=r.json()
    if obj.get("status")!="000": raise RuntimeError(f"DART {path}: {obj.get('status')} {obj.get('message')}")
    return obj

def match_account(name,aliases):
    n=str(name or "").strip().lower()
    return any(a.lower() in n or n in a.lower() for a in aliases)

def extract(rows,key):
    for row in rows:
        if match_account(row.get("account_nm"),ACCOUNTS[key]):
            for field in ("thstrm_amount","thstrm_add_amount"):
                value=num(row.get(field))
                if value is not None: return value
    return None

def period_end(year,code):
    return {"11011":f"{year}-12-31","11012":f"{year}-06-30","11013":f"{year}-03-31","11014":f"{year}-09-30"}[code]

def fetch_year(year,code):
    obj=api_get("fnlttSinglAcntAll",{"corp_code":CORP_CODE,"bsns_year":str(year),"reprt_code":code,"fs_div":"CFS"})
    (RAW/f"{year}_{code}.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
    rows=obj.get("list",[])
    if not rows: return None
    out={"fiscal_year":year,"period_end":period_end(year,code),"period_type":REPORTS[code],"report_code":code,
         "report_name":REPORT_NAMES[code],"corp_code":CORP_CODE,"stock_code":STOCK_CODE,
         "currency_unit":next((r.get("currency") for r in rows if r.get("currency")),""),
         "rcept_no":next((r.get("rcept_no") for r in rows if r.get("rcept_no")),"")}
    for key in ACCOUNTS: out[key]=extract(rows,key)
    out["dart_url"]=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={out['rcept_no']}" if out["rcept_no"] else ""
    return out

def safe_fetch(year,code):
    try: return fetch_year(year,code)
    except Exception as e:
        print(f"[WARN] {year} {code}: {e}"); return None

def collect_report_index():
    rows=[]
    for year in range(START_YEAR,END_YEAR+1):
        try:
            obj=api_get("list",{"corp_code":CORP_CODE,"bgn_de":f"{year}0101","end_de":f"{year}1231","page_no":"1","page_count":"100"})
            for r in obj.get("list",[]):
                nm=r.get("report_nm","")
                if any(k in nm for k in ("사업보고서","반기보고서","분기보고서")):
                    rows.append({"fiscal_year":year,"report_name":nm,"report_date":r.get("rcept_dt",""),
                                  "rcept_no":r.get("rcept_no",""),"corp_name":r.get("corp_name",""),
                                  "dart_url":f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r.get('rcept_no','')}"})
        except Exception as e: print(f"[WARN] report index {year}: {e}")
        time.sleep(.12)
    if rows: pd.DataFrame(rows).drop_duplicates("rcept_no").sort_values("report_date").to_csv(DATA/"reports.csv",index=False,encoding="utf-8-sig")

def add_derived(df):
    df=df.copy()
    for c in ["revenue","gross_profit","operating_income","net_income","total_assets","total_liabilities","total_equity","cash","cfo","capex","interest_expense","interest_bearing_debt","current_assets","current_liabilities"]:
        if c not in df: df[c]=pd.NA
        df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.sort_values(["period_type","period_end"])
    df["gross_margin"]=df.gross_profit/df.revenue; df["operating_margin"]=df.operating_income/df.revenue; df["net_margin"]=df.net_income/df.revenue
    df["debt_ratio"]=df.total_liabilities/df.total_equity; df["equity_ratio"]=df.total_equity/df.total_assets; df["current_ratio"]=df.current_assets/df.current_liabilities
    df["fcf"]=df.cfo-df.capex.abs(); df["net_debt"]=df.interest_bearing_debt-df.cash
    df["interest_coverage"]=df.operating_income/df.interest_expense.abs(); df["asset_turnover"]=df.revenue/df.total_assets
    df["cfo_to_net_income"]=df.cfo/df.net_income; df["revenue_growth"]=df.groupby("period_type").revenue.pct_change()
    for base,outcol in [("total_assets","roa"),("total_equity","roe")]:
        prev=df.groupby("period_type")[base].shift(1); df[outcol]=df.net_income/((df[base]+prev)/2)
    return df

def main():
    if not API_KEY: raise SystemExit("DART_API_KEY is required.")
    jobs=[(year,code) for year in range(START_YEAR,END_YEAR+1) for code in REPORTS]
    rows=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(safe_fetch,y,c) for y,c in jobs]):
            item=f.result()
            if item: rows.append(item)
    collect_report_index()
    fresh=pd.DataFrame(rows)
    if fresh.empty: raise SystemExit("No structured DART financial rows returned.")
    annual=fresh[fresh.period_type.eq("annual")].copy(); annual["period_label"]=annual.fiscal_year.astype(str)
    half=fresh[fresh.period_type.eq("half")].copy(); half["period_label"]=half.fiscal_year.astype(str)+" H1"
    q=fresh[fresh.period_type.eq("quarterly")].copy(); q["period_label"]=q.period_end.str[:4]+" "+q.report_code.map({"11013":"Q1","11014":"Q3"}).fillna("")
    fresh=pd.concat([annual,half,q],ignore_index=True,sort=False)
    legacy_path=MANUAL/"legacy_2010_2014.csv"
    legacy=pd.read_csv(legacy_path) if legacy_path.exists() and legacy_path.stat().st_size else pd.DataFrame()
    df=pd.concat([legacy,fresh],ignore_index=True,sort=False) if not legacy.empty else fresh
    df=add_derived(df).drop_duplicates(["fiscal_year","period_type","period_end"],keep="last").sort_values(["period_end","period_type"])
    df.to_csv(DATA/"financials.csv",index=False,encoding="utf-8-sig")
    status={"updated_at_utc":datetime.utcnow().isoformat(timespec="seconds")+"Z","rows":len(df),"start_year":int(pd.to_numeric(df.fiscal_year,errors="coerce").min()),"latest_period":str(df.period_end.max()),"legacy_2010_2014_present":bool(not legacy.empty)}
    (DATA/"status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(status,ensure_ascii=False))
if __name__=="__main__": main()
