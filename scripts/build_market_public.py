import json,os,datetime
try:
 import akshare as ak
except Exception as e:
 raise SystemExit('akshare unavailable: '+str(e))
# Public AkShare snapshot; source availability can vary, so fail clearly rather than fabricate data.
df=ak.stock_zh_a_spot_em()
cols={'代码':'code','名称':'name','最新价':'price','涨跌幅':'pct_chg','成交量':'volume','成交额':'amount','换手率':'turnover','市盈率-动态':'pe','市净率':'pb'}
for a,b in cols.items():
 if a not in df.columns: df[b]=None
 else: df[b]=df[a]
keep=['code','name','price','pct_chg','volume','amount','turnover','pe','pb']
rows=df[keep].where(df[keep].notna(),None).to_dict('records')
os.makedirs('data',exist_ok=True)
with open('data/market.json','w',encoding='utf-8') as f: json.dump({'version':'5.2-public','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'AkShare public market endpoint','stocks':rows},f,ensure_ascii=False)
print('market rows:',len(rows))
