import os, json, time, zipfile, io
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd

API=os.environ.get("DART_API_KEY")
if not API:
    raise SystemExit("DART_API_KEY 환경변수를 설정하세요.")
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"; DATA.mkdir(exist_ok=True)
BASE="https://opendart.fss.or.kr/api"
CORP="00000000"  # replaced below by corp-code lookup

def get_json(endpoint, params):
    params={**params,"crtfc_key":API}
    r=requests.get(f"{BASE}/{endpoint}",params=params,timeout=60); r.raise_for_status()
    return r.json()

def corp_code():
    z=requests.get(f"{BASE}/corpCode.xml",params={"crtfc_key":API},timeout=60); z.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(z.content)) as f:
        import xml.etree.ElementTree as ET
        root=ET.fromstring(f.read("CORPCODE.xml"))
    for c in root.findall("list"):
        if c.findtext("corp_name") in ("SK하이닉스","에스케이하이닉스"):
            return c.findtext("corp_code")
    raise RuntimeError("corpCode.xml에서 SK하이닉스 코드를 찾지 못했습니다.")

def reports(code):
    rows=[]
    for year in range(2010,datetime.now().year+1):
        for reprt, label in [("11011","annual"),("11012","half-year"),("11013","quarterly"),("11014","quarterly")]:
            j=get_json("list.json",{"corp_code":code,"bgn_de":f"{year}0101","end_de":f"{year}1231","pblntf_ty":"A","page_no":1,"page_count":100})
            if j.get("status") not in ("000","013"): continue
            for x in j.get("list",[]):
                if x.get("reprt_code")==reprt and x.get("rcept_no") and x.get("rcept_no") not in {a["rcept_no"] for a in rows}:
                    x["period_type"]=label; rows.append(x)
        time.sleep(.1)
    return rows

ALIASES={
 "매출액":["매출액","수익(매출액)","영업수익"],
 "영업이익":["영업이익","영업이익(손실)"],
 "당기순이익":["당기순이익","당기순이익(손실)","분기순이익","반기순이익"],
 "자산총계":["자산총계"],"부채총계":["부채총계"],"자본총계":["자본총계"],
 "현금및현금성자산":["현금및현금성자산","현금 및 현금성자산"],
 "영업활동현금흐름":["영업활동현금흐름","영업활동으로 인한 현금흐름"]
}
def choose(df, names):
    s=df[df["account_nm"].isin(names)]
    if s.empty: return None
    # prefer consolidated (CFS), then latest available current period amount
    s=s.copy(); s["pref"]=s["fs_div"].map({"CFS":0,"OFS":1}).fillna(2)
    s=s.sort_values(["pref"])
    for col in ("thstrm_amount","thstrm_add_amount"):
        if col in s:
            for v in s[col]:
                try:
                    if pd.notna(v) and str(v).strip() not in ("","-"): return float(str(v).replace(",",""))
                except ValueError: pass
    return None

def main():
    code=corp_code(); reports_list=reports(code)
    raw=[]; normalized=[]
    for r in reports_list:
        j=get_json("fnlttSinglAcntAll.json",{"corp_code":code,"bsns_year":r["bsns_year"],"reprt_code":r["reprt_code"],"fs_div":"CFS"})
        if j.get("status")!="000":
            j=get_json("fnlttSinglAcntAll.json",{"corp_code":code,"bsns_year":r["bsns_year"],"reprt_code":r["reprt_code"],"fs_div":"OFS"})
        raw.append({"receipt":r["rcept_no"],"response":j})
        rows=j.get("list",[])
        if not rows: continue
        df=pd.DataFrame(rows)
        vals={k:choose(df,v) for k,v in ALIASES.items()}
        vals.update({"year":int(r["bsns_year"]),"report_code":r["reprt_code"],"report_name":r.get("report_nm",""),"period_type":r["period_type"],"receipt_no":r["rcept_no"],"filing_date":r.get("rcept_dt","")})
        def ratio(a,b): return (a/b*100) if a is not None and b not in (None,0) else None
        vals["영업이익률(%)"]=ratio(vals["영업이익"],vals["매출액"])
        vals["순이익률(%)"]=ratio(vals["당기순이익"],vals["매출액"])
        vals["부채비율(%)"]=ratio(vals["부채총계"],vals["자본총계"])
        vals["ROE(%)"]=ratio(vals["당기순이익"],vals["자본총계"])
        vals["ROA(%)"]=ratio(vals["당기순이익"],vals["자산총계"])
        normalized.append(vals); time.sleep(.12)
    out=pd.DataFrame(normalized).sort_values(["year","report_code"])
    out.to_csv(DATA/"financials.csv",index=False,encoding="utf-8-sig")
    (DATA/"financials.json").write_text(out.to_json(orient="records",force_ascii=False),encoding="utf-8")
    (DATA/"raw_api.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding="utf-8")
    (DATA/"reports.json").write_text(json.dumps(reports_list,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"완료: 보고서 {len(reports_list)}건, 재무 데이터 {len(normalized)}건")

if __name__=="__main__": main()
