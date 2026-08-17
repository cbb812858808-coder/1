import datetime,json,os,time,requests
OUT='data/history.json'; UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
# Build recent daily K-lines for the strongest liquid universe. Public EastMoney historical endpoint; no token.
def get(code,market):
 url='https://push2his.eastmoney.com/api/qt/stock/kline/get'
 p={'secid':f'{market}.{code}','klt':101,'fqt':1,'beg':(datetime.date.today()-datetime.timedelta(days=150)).strftime('%Y%m%d'),'end':'20500101','fields1':'f1,f2,f3,f4,f5,f6','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61','ut':'fa5fd1943c7b386f172d6893dbfba10b'}
 r=requests.get(url,params=p,headers={'User-Agent':UA,'Referer':'https://quote.eastmoney.com/'},timeout=10);r.raise_for_status();d=(r.json().get('data') or {});kl=d.get('klines') or []
 out=[]
 for s in kl:
  a=s.split(',');
  if len(a)>=7:out.append({'date':a[0],'open':float(a[1]),'close':float(a[2]),'high':float(a[3]),'low':float(a[4]),'volume':float(a[5]),'amount':float(a[6])})
 return out
# Keep file compact: history for top 500 by turnover from market snapshot.
m=json.load(open('data/market.json',encoding='utf8'));stocks=m.get('stocks',[]);stocks=sorted(stocks,key=lambda x:float(x.get('amount') or 0),reverse=True)[:500]
out={}
for i,x in enumerate(stocks):
 code=x['code']; market='1' if code.startswith(('6','68')) else '0'
 try:
  k=get(code,market)
  if len(k)>=60:out[code]=k
 except Exception:pass
 if i%25==0:time.sleep(.2)
os.makedirs('data',exist_ok=True);json.dump({'version':'5.5-history','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stocks':out},open(OUT,'w',encoding='utf8'),ensure_ascii=False)
print('history stocks',len(out))
