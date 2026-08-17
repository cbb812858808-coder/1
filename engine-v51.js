/* A股AI选股5.1 数据/评分引擎：前端安全适配层。默认离线；配置 API_BASE 后可接你的后端。 */
window.AI51={version:'5.1',apiBase:'',weights:{fund:30,tech:30,flow:15,sector:10,global:5,small:5,catalyst:5},excluded:['688','ST','*ST']};
AI51.fetchJSON=async function(path,ms=5000){if(!AI51.apiBase)throw Error('未配置实时数据服务');const c=new AbortController(),t=setTimeout(()=>c.abort(),ms);try{const r=await fetch(AI51.apiBase+path,{cache:'no-store',signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}finally{clearTimeout(t)}};
AI51.ma=function(a,n){if(!a||a.length<n)return null;return a.slice(-n).reduce((s,x)=>s+Number(x),0)/n};
AI51.score=function(x){const fund=Number(x.fund||0),tech=Number(x.tech||0),flow=Number(x.flow||0),sector=Number(x.sector||0),global=Number(x.global||0),small=Number(x.small||0),cat=Number(x.catalyst||0),risk=Number(x.risk||0);return Math.max(0,Math.min(100,Math.round(fund*.30+tech*.30+flow*.15+sector*.10+global*.05+small*.05+cat*.05-risk*.35)))};
AI51.excludedStock=function(code,name){code=String(code||'');name=String(name||'');return code.startsWith('688')||code.startsWith('8')||code.startsWith('4')||name.includes('ST')||name.includes('*ST')};
AI51.explain=function(x){const a=[];if(x.maBull)a.push('5/10/20日均线多头');if(x.breakout)a.push('突破');if(x.volumeBreak)a.push('放量');if(x.pullback)a.push('回踩确认');if(x.macd)a.push('MACD强化');if(Number(x.flow)>70)a.push('资金流入');return a.length?a.join(' + '):'综合评分';};
AI51.scan=function(rows){return (rows||[]).filter(x=>!AI51.excludedStock(x.code,x.name)).map(x=>({...x,score:AI51.score(x),reason:AI51.explain(x)})).sort((a,b)=>b.score-a.score)};
