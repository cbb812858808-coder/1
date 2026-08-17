import os,json,requests,datetime
TOKEN=os.environ['TUSHARE_TOKEN']; API='https://api.tushare.pro'; today=datetime.date.today().strftime('%Y%m%d')
def call(api_name,params={},fields=''):
 r=requests.post(API,json={'api_name':api_name,'token':TOKEN,'params':params,'fields':fields},timeout=30); r.raise_for_status(); d=r.json();
 if d.get('code',0)!=0: raise RuntimeError(d)
 return d.get('data',{})
# 基础股票池：全A股，前端再剔除科创板/ST；Tushare stock_basic覆盖全市场A股。
b=call('stock_basic',{'exchange':'','list_status':'L'},'ts_code,symbol,name,industry,market')
cols=b.get('fields',[]); rows=[dict(zip(cols,x)) for x in b.get('items',[])]
# 最近交易日行情（若当天盘中无日线，则回退到最近可用交易日）
d=call('daily',{'trade_date':today},'ts_code,trade_date,open,high,low,close,pre_close,vol,amount,pct_chg')
cols=d.get('fields',[]); daily=[dict(zip(cols,x)) for x in d.get('items',[])]
by={x['ts_code']:x for x in daily}
out=[]
for s in rows:
 q=by.get(s['ts_code']);
 if not q: continue
 out.append({**s,**q})
os.makedirs('data',exist_ok=True)
json.dump({'version':'5.2','generated_at':datetime.datetime.utcnow().isoformat()+'Z','trade_date':today,'source':'Tushare Pro','stocks':out},open('data/market.json','w',encoding='utf8'),ensure_ascii=False)
print('stocks',len(out))
