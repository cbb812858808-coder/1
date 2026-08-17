import datetime,json,os,requests,random
from concurrent.futures import ThreadPoolExecutor,as_completed
OUT='data/history.json'
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
HOSTS=['push2his.eastmoney.com','82.push2his.eastmoney.com','56.push2his.eastmoney.com']

def get(item):
    code=str(item['code']); market='1' if code.startswith(('6','68')) else '0'
    params={'secid':f'{market}.{code}','klt':101,'fqt':1,'beg':(datetime.date.today()-datetime.timedelta(days=220)).strftime('%Y%m%d'),'end':'20500101','fields1':'f1,f2,f3,f4,f5,f6','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61','ut':'fa5fd1943c7b386f172d6893dbfba10b'}
    last=''
    for host in HOSTS:
        try:
            r=requests.get('https://'+host+'/api/qt/stock/kline/get',params=params,headers={'User-Agent':UA,'Referer':'https://quote.eastmoney.com/','Accept':'application/json, text/plain, */*'},timeout=8)
            r.raise_for_status(); kl=((r.json().get('data') or {}).get('klines') or [])
            out=[]
            for s in kl:
                a=s.split(',')
                if len(a)>=7:
                    try: out.append({'date':a[0],'open':float(a[1]),'close':float(a[2]),'high':float(a[3]),'low':float(a[4]),'volume':float(a[5]),'amount':float(a[6])})
                    except ValueError: pass
            if len(out)>=60:return code,out,None
            last=f'{host}:{len(out)}'
        except Exception as e:last=f'{host}:{type(e).__name__}'
    return code,None,last

m=json.load(open('data/market.json',encoding='utf8'))
# Candidate pool: liquid, positive momentum, and high turnover; exclude STAR/ST.
def valid(x):
    c=str(x.get('code','')); n=str(x.get('name',''))
    return not (c.startswith(('688','8','4')) or 'ST' in n.upper())
def score(x):
    p=float(x.get('pct_chg') or 0); t=float(x.get('turnover') or 0); a=float(x.get('amount') or 0)
    return max(-20,min(100,p*5))+min(30,t*2)+min(30,(a/1e8)*3)
stocks=sorted((x for x in m.get('stocks',[]) if valid(x)),key=score,reverse=True)[:100]
out={};errors=0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs=[ex.submit(get,x) for x in stocks]
    for f in as_completed(futs):
        code,k,err=f.result()
        if k is not None: out[code]=k
        else: errors+=1
os.makedirs('data',exist_ok=True)
json.dump({'version':'5.5-history-fast','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_count':len(stocks),'stocks':out},open(OUT,'w',encoding='utf8'),ensure_ascii=False)
print('history candidates',len(stocks),'history stocks',len(out),'errors',errors)
