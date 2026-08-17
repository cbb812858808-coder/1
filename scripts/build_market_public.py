import datetime, json, os, time
import requests

OUT = "data/market.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

def normalize(rows, source):
    out = []
    for r in rows or []:
        code = str(r.get("code", "")).zfill(6)
        name = str(r.get("name", ""))
        try: price = float(r.get("price") or 0)
        except: price = 0
        try: pct = float(r.get("pct_chg") or 0)
        except: pct = 0
        try: turnover = float(r.get("turnover") or 0)
        except: turnover = 0
        if len(code) == 6 and price > 0:
            out.append({"code": code, "name": name, "price": price, "pct_chg": pct,
                        "volume": r.get("volume"), "amount": r.get("amount"),
                        "turnover": turnover, "pe": r.get("pe"), "pb": r.get("pb"),
                        "source": source})
    return out

def eastmoney():
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1, "pz": 6000, "po": 1, "np": 1, "fltt": 2, "invt": 2,
        "fid": "f3", "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f12,f14,f2,f3,f5,f6,f8,f9,f10"
    }
    r = requests.get(url, params=params, headers={"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"}, timeout=12)
    r.raise_for_status()
    data = r.json().get("data") or {}
    rows = []
    for x in data.get("diff") or []:
        rows.append({"code": x.get("f12"), "name": x.get("f14"), "price": x.get("f2"),
                     "pct_chg": x.get("f3"), "volume": x.get("f5"), "amount": x.get("f6"),
                     "turnover": x.get("f8"), "pe": x.get("f9"), "pb": x.get("f10")})
    rows = normalize(rows, "EastMoney public snapshot")
    if len(rows) < 1000: raise RuntimeError(f"EastMoney returned only {len(rows)} rows")
    return rows

def akshare():
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    cols = {"代码":"code","名称":"name","最新价":"price","涨跌幅":"pct_chg","成交量":"volume","成交额":"amount","换手率":"turnover","市盈率-动态":"pe","市净率":"pb"}
    for a,b in cols.items():
        if a not in df.columns: df[b] = None
        else: df[b] = df[a]
    return normalize(df[["code","name","price","pct_chg","volume","amount","turnover","pe","pb"]].where(df.notna(), None).to_dict("records"), "AkShare public snapshot")

def fetch():
    errors=[]
    for fn in (eastmoney, akshare):
        try:
            rows=fn()
            if rows:
                return rows
        except Exception as e:
            errors.append(type(e).__name__+": "+str(e)[:180])
            time.sleep(1)
    raise RuntimeError("all public sources failed: " + " | ".join(errors))

rows=fetch()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
now=datetime.datetime.now(datetime.timezone.utc)
with open(OUT,"w",encoding="utf-8") as f:
    json.dump({"version":"5.3-public-multisource","generated_at":now.isoformat(),"trade_date":now.date().isoformat(),"source":rows[0].get("source"),"stocks":rows},f,ensure_ascii=False)
print("market rows:",len(rows),"source:",rows[0].get("source"))
