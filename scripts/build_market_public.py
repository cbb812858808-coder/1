import datetime,json,os,time,requests,random
OUT='data/market.json'
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
FIELDS='f12,f13,f14,f2,f3,f5,f6,f8,f9,f10'
FS='m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048'

def normalize(rows,source):
 out=[]
 for r in rows or []:
  code=str(r.get('code','')).zfill(6); name=str(r.get('name',''))
  try:p=float(r.get('price') or 0)
  except:p=0
  try:pct=float(r.get('pct_chg') or 0)
  except:pct=0
  if len(code)==6 and p>0:out.append({'code':code,'name':name,'price':p,'pct_chg':pct,'volume':r.get('volume'),'amount':r.get('amount'),'turnover':r.get('turnover'),'pe':r.get('pe'),'pb':r.get('pb'),'source':source})
 return out

def eastmoney_host(host):
 s=requests.Session();s.headers.update({'User-Agent':UA,'Accept':'application/json, text/plain, */*','Referer':'https://quote.eastmoney.com/','Connection':'keep-alive'})
 rows=[];pn=1;pz=100
 while pn<=80:
  q={'pn':pn,'pz':pz,'po':1,'np':1,'ut':'bd1d9ddb04089700cf9c27f6f7426281','fltt':2,'invt':2,'fid':'f3','fs':FS,'fields':FIELDS,'_':str(int(time.time()*1000))}
  last=None
  for attempt in range(3):
   try:
    r=s.get(f'https://{host}/api/qt/clist/get',params=q,timeout=15);r.raise_for_status();last=r;break
   except Exception:
    if attempt==2:raise
    time.sleep(.6*(attempt+1)+random.random()*.3)
  data=last.json().get('data') or {};diff=data.get('diff') or []
  if not diff:break
  rows += [{'code':x.get('f12'),'name':x.get('f14'),'price':x.get('f2'),'pct_chg':x.get('f3'),'volume':x.get('f5'),'amount':x.get('f6'),'turnover':x.get('f8'),'pe':x.get('f9'),'pb':x.get('f10')} for x in diff]
  total=int(data.get('total') or 0)
  if len(rows)>=total or len(diff)<pz:break
  pn+=1;time.sleep(.15)
 rows=normalize(rows,f'EastMoney public snapshot ({host})')
 if len(rows)<1000:raise RuntimeError(f'{host} returned only {len(rows)} rows')
 return rows

def akshare():
 import akshare as ak
 df=ak.stock_zh_a_spot_em();mp={'代码':'code','名称':'name','最新价':'price','涨跌幅':'pct_chg','成交量':'volume','成交额':'amount','换手率':'turnover','市盈率-动态':'pe','市净率':'pb'}
 for a,b in mp.items():df[b]=df[a] if a in df.columns else None
 return normalize(df[list(mp.values())].where(df.notna(),None).to_dict('records'),'AkShare public snapshot')

def fetch():
 errors=[]
 # Delay endpoints are a useful fallback when realtime push hosts reject CI traffic.
 for host in ['82.push2delay.eastmoney.com','push2delay.eastmoney.com','82.push2.eastmoney.com','push2.eastmoney.com','56.push2.eastmoney.com']:
  try:return eastmoney_host(host)
  except Exception as e:errors.append(host+': '+type(e).__name__+': '+str(e)[:140]);time.sleep(1)
 try:return akshare()
 except Exception as e:errors.append('AkShare: '+type(e).__name__+': '+str(e)[:140])
 raise RuntimeError('all public sources failed: '+' | '.join(errors))

rows=fetch();os.makedirs('data',exist_ok=True);now=datetime.datetime.now(datetime.timezone.utc)
with open(OUT,'w',encoding='utf8') as f:json.dump({'version':'5.4-public-multisource','generated_at':now.isoformat(),'trade_date':now.date().isoformat(),'source':rows[0]['source'],'stocks':rows},f,ensure_ascii=False)
print('market rows:',len(rows),'source:',rows[0]['source'])
