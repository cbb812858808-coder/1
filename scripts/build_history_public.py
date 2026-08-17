import datetime,json,os,time,requests,random
OUT='data/history.json'
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
HOSTS=['push2his.eastmoney.com','82.push2his.eastmoney.com','push2his.eastmoney.com','56.push2his.eastmoney.com']

def get(code,market):
    params={'secid':f'{market}.{code}','klt':101,'fqt':1,'beg':(datetime.date.today()-datetime.timedelta(days=220)).strftime('%Y%m%d'),'end':'20500101','fields1':'f1,f2,f3,f4,f5,f6','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61','ut':'fa5fd1943c7b386f172d6893dbfba10b'}
    last=None
    for host in HOSTS:
        try:
            r=requests.get('https://'+host+'/api/qt/stock/kline/get',params=params,headers={'User-Agent':UA,'Referer':'https://quote.eastmoney.com/','Accept':'application/json, text/plain, */*'},timeout=12)
            r.raise_for_status(); d=r.json().get('data') or {}; kl=d.get('klines') or []
            out=[]
            for s in kl:
                a=s.split(',')
                if len(a)>=7:
                    try: out.append({'date':a[0],'open':float(a[1]),'close':float(a[2]),'high':float(a[3]),'low':float(a[4]),'volume':float(a[5]),'amount':float(a[6])})
                    except ValueError: pass
            if len(out)>=60:return out
            last=f'{host} returned {len(out)} rows'
        except Exception as e:last=f'{host}: {type(e).__name__}: {str(e)[:100]}'
        time.sleep(.25+random.random()*.25)
    raise RuntimeError(last or 'history request failed')

m=json.load(open('data/market.json',encoding='utf8'));stocks=sorted(m.get('stocks',[]),key=lambda x:float(x.get('amount') or 0),reverse=True)[:500];out={};errors=0
for i,x in enumerate(stocks):
    code=str(x['code']); market='1' if code.startswith(('6','68')) else '0'
    try: out[code]=get(code,market)
    except Exception: errors+=1
    if i%20==0: time.sleep(.2)
os.makedirs('data',exist_ok=True)
with open(OUT,'w',encoding='utf8') as f:json.dump({'version':'5.5-history-multihost','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stocks':out},f,ensure_ascii=False)
print('history stocks',len(out),'errors',errors)
