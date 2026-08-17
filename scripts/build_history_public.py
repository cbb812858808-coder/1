import datetime,json,os,requests
from concurrent.futures import ThreadPoolExecutor,as_completed
OUT='data/history.json'
UA='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1'

START=(datetime.date.today()-datetime.timedelta(days=260)).strftime('%Y%m%d')
END=datetime.date.today().strftime('%Y%m%d')
S=requests.Session(); S.headers.update({'User-Agent':UA,'Accept':'application/json,text/plain,*/*','Connection':'keep-alive'})

def parse_rows(rows):
    out=[]
    for s in rows or []:
        a=s.split(',') if isinstance(s,str) else s
        if len(a)>=7:
            try:
                out.append({'date':a[0],'open':float(a[1]),'close':float(a[2]),'high':float(a[3]),'low':float(a[4]),'volume':float(a[5]),'amount':float(a[6])})
            except (TypeError,ValueError): pass
    return out

def eastmoney(code):
    market='1' if code.startswith('6') else '0'
    p={'secid':f'{market}.{code}','klt':101,'fqt':1,'beg':START,'end':END,'fields1':'f1,f2,f3,f4,f5,f6','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61','ut':'fa5fd1943c7b386f172d6893dbfba10b'}
    for host in ('push2his.eastmoney.com','push2his.eastmoney.com'):
        try:
            r=S.get('https://'+host+'/api/qt/stock/kline/get',params=p,headers={'Referer':'https://quote.eastmoney.com/'},timeout=5)
            r.raise_for_status(); d=r.json().get('data') or {}; out=parse_rows(d.get('klines'))
            if len(out)>=60:return out,'eastmoney'
        except Exception: pass
    return None,None

def tencent(code):
    prefix='sh' if code.startswith('6') else 'sz'
    url=f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={prefix}{code},day,,,260,qfq'
    try:
        r=S.get(url,timeout=6); r.raise_for_status(); root=r.json().get('data') or {}; d=root.get(prefix+code) or {}
        rows=d.get('qfqday') or d.get('day') or []
        out=parse_rows(rows)
        if len(out)>=60:return out,'tencent'
    except Exception: pass
    return None,None

def sina(code):
    prefix='sh' if code.startswith('6') else 'sz'
    try:
        url=f'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={prefix}{code}&scale=240&ma=no&datalen=260'
        r=S.get(url,timeout=6); r.raise_for_status(); rows=r.json(); out=[]
        for a in rows or []:
            try: out.append({'date':a['day'],'open':float(a['open']),'close':float(a['close']),'high':float(a['high']),'low':float(a['low']),'volume':float(a.get('volume',0)),'amount':float(a.get('amount',0))})
            except (KeyError,TypeError,ValueError): pass
        if len(out)>=60:return out,'sina'
    except Exception: pass
    return None,None

def get(item):
    code=str(item['code'])
    for fn in (tencent,eastmoney,sina):
        out,src=fn(code)
        if out:return code,out,src
    return code,None,'all_failed'

m=json.load(open('data/market.json',encoding='utf8'))
def valid(x):
    c=str(x.get('code','')); n=str(x.get('name',''))
    return not (c.startswith(('688','8','4')) or 'ST' in n.upper())
def score(x):
    p=float(x.get('pct_chg') or 0); t=float(x.get('turnover') or 0); a=float(x.get('amount') or 0)
    return max(-20,min(100,p*5))+min(30,t*2)+min(30,(a/1e8)*3)
stocks=sorted((x for x in m.get('stocks',[]) if valid(x)),key=score,reverse=True)[:100]
out={}; sources={}; errors=0
with ThreadPoolExecutor(max_workers=12) as ex:
    futs=[ex.submit(get,x) for x in stocks]
    for f in as_completed(futs):
        code,k,src=f.result()
        if k is not None: out[code]=k; sources[code]=src
        else: errors+=1
os.makedirs('data',exist_ok=True)
json.dump({'version':'5.6-history-multi-source','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_count':len(stocks),'stocks':out,'sources':sources,'success_count':len(out),'error_count':errors},open(OUT,'w',encoding='utf8'),ensure_ascii=False)
print('history candidates',len(stocks),'history stocks',len(out),'errors',errors,'sources',json.dumps({s:list(sources.values()).count(s) for s in set(sources.values())}))
