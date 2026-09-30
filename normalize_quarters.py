from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"
FLOW=["revenue","gross_profit","sga","operating_income","pretax_income","net_income","net_income_parent","cfo","cfi","cff","capex","interest_expense"]

def subtract(upper,lower,label,year):
    out=upper.copy()
    out["period_type"]="quarterly"; out["period_label"]=f"{year} {label}"
    out["period_end"]={"Q2":f"{year}-06-30","Q3":f"{year}-09-30","Q4":f"{year}-12-31"}[label]
    for c in FLOW:
        a=pd.to_numeric(upper.get(c),errors="coerce"); b=pd.to_numeric(lower.get(c),errors="coerce")
        out[c]=a-b if pd.notna(a) and pd.notna(b) else pd.NA
    return out

def main():
    p=DATA/"financials.csv"; df=pd.read_csv(p)
    if df.empty: return
    annual=df[df.period_type.eq("annual")].copy(); annual["period_label"]=annual.fiscal_year.astype(str)
    half=df[df.period_type.eq("half")].copy(); half["period_label"]=half.fiscal_year.astype(str)+" H1"
    q1=df[(df.period_type.eq("quarterly"))&(df.report_code.astype(str).eq("11013"))]
    q3=df[(df.period_type.eq("quarterly"))&(df.report_code.astype(str).eq("11014"))]
    rows=[]
    for y in sorted(pd.to_numeric(df.fiscal_year,errors="coerce").dropna().astype(int).unique()):
        a=annual[annual.fiscal_year.eq(y)]; h=half[half.fiscal_year.eq(y)]
        one=q1[q1.fiscal_year.eq(y)]; three=q3[q3.fiscal_year.eq(y)]
        if not one.empty: rows.append(one.iloc[0].to_dict()|{"period_type":"quarterly","period_label":f"{y} Q1"})
        if not h.empty and not one.empty: rows.append(subtract(h.iloc[0].to_dict(),one.iloc[0].to_dict(),"Q2",y))
        if not three.empty and not h.empty: rows.append(subtract(three.iloc[0].to_dict(),h.iloc[0].to_dict(),"Q3",y))
        if not a.empty and not three.empty: rows.append(subtract(a.iloc[0].to_dict(),three.iloc[0].to_dict(),"Q4",y))
    out=pd.concat([annual,half,pd.DataFrame(rows)],ignore_index=True,sort=False)
    for c in ["revenue","gross_profit","operating_income","net_income","total_assets","total_liabilities","total_equity","cash","cfo","capex","current_assets","current_liabilities","interest_bearing_debt","interest_expense"]:
        if c in out: out[c]=pd.to_numeric(out[c],errors="coerce")
    out["gross_margin"]=out.gross_profit/out.revenue; out["operating_margin"]=out.operating_income/out.revenue; out["net_margin"]=out.net_income/out.revenue
    out["current_ratio"]=out.current_assets/out.current_liabilities; out["debt_ratio"]=out.total_liabilities/out.total_equity; out["equity_ratio"]=out.total_equity/out.total_assets
    out["fcf"]=out.cfo-out.capex.abs(); out["net_debt"]=out.interest_bearing_debt-out.cash; out["interest_coverage"]=out.operating_income/out.interest_expense.abs()
    out["asset_turnover"]=out.revenue/out.total_assets; out["cfo_to_net_income"]=out.cfo/out.net_income
    for base,outcol in [("total_assets","roa"),("total_equity","roe")]:
        prev=out.groupby("period_type")[base].shift(1); out[outcol]=out.net_income/((out[base]+prev)/2)
    out=out.drop_duplicates(["fiscal_year","period_type","period_end"],keep="last").sort_values(["period_end","period_type"])
    out.to_csv(p,index=False,encoding="utf-8-sig")

if __name__=="__main__": main()
