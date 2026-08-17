import json,datetime,os
from statistics import mean
IN='data/history.json';OUT='data/ai_scores.json'
def avg(a,n): return mean(a[-n:])
def ema(a,n):
 k=2/(n+1);e=a[0]
 for x in a[1:]:e=x*k+e*(1-k)
 return e
def calc(k):
 c=[x['close'] for x in k];h=[x['high'] for x in k];l=[x['low'] for x in k];v=[x['volume'] for x in k]
 ma5,ma10,ma20,ma60=[avg(c,n) for n in(5,10,20,60)]; mac=[ema(c[:i+1],12)-ema(c[:i+1],26) for i in range(len(c))];macd=mac[-1];sig=ema(mac,9);hist=macd-sig
 g=[max(c[i]-c[i-1],0) for i in range(1,len(c))];loss=[max(c[i-1]-c[i],0) for i in range(1,len(c))];ag=avg(g,14);al=avg(loss,14);rsi=100 if al==0 else 100-100/(1+ag/al)
 ll=min(l[-9:]);hh=max(h[-9:]);kdjk=50 if hh==ll else(c[-1]-ll)/(hh-ll)*100;kdjd=mean([kdjk]);kdjj=3*kdjk-2*kdjd
 vol5=avg(v,5);vol20=avg(v,20);high20=max(h[-20:]);high60=max(h[-60:]);tech=0;reasons=[];risk=0
 if ma5>ma10>ma20>ma60:tech+=8;reasons.append('均线多头')
 elif ma5>ma10>ma20:tech+=5;reasons.append('短中期转强')
 if c[-1]>=high20*.995:tech+=6;reasons.append('20日突破')
 if c[-1]>=high60*.995:tech+=5;reasons.append('60日突破')
 if macd>sig and hist>0:tech+=6;reasons.append('MACD强化')
 elif macd>sig:tech+=4;reasons.append('MACD金叉区')
 if vol5>vol20*1.3:tech+=3;reasons.append('放量')
 if 45<=rsi<=75:tech+=2
 if kdjk>kdjd and kdjj>50:tech+=2;reasons.append('KDJ转强')
 if rsi>85:risk+=5;reasons.append('RSI过热')
 if c[-1]<ma20*.97:risk+=5;reasons.append('跌破20日线')
 tech=min(30,tech);base=15;funds=10 if vol5>vol20 else 5;industry=5;glob=2.5;small=2.5;cat=3 if c[-1]>=high20*.995 else 1
 total=max(0,min(100,base+tech+funds+industry+glob+small+cat-risk))
 return {'score':round(total,1),'fundamental':base,'technical':tech,'funds':funds,'industry':industry,'global':glob,'small_cap':small,'catalyst':cat,'risk_deduction':risk,'reasons':reasons,'ma5':round(ma5,3),'ma10':round(ma10,3),'ma20':round(ma20,3),'ma60':round(ma60,3),'rsi':round(rsi,1),'macd':round(macd,4),'macd_signal':round(sig,4),'kdj_k':round(kdjk,1)}
j=json.load(open(IN,encoding='utf8'));out=[]
for code,k in j.get('stocks',{}).items():
 if len(k)>=60:out.append({'code':code,**calc(k),'latest':k[-1]})
out.sort(key=lambda x:x['score'],reverse=True);os.makedirs('data',exist_ok=True);json.dump({'version':'5.5-ai-score','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'count':len(out),'stocks':out},open(OUT,'w',encoding='utf8'),ensure_ascii=False);print('AI scored',len(out))
