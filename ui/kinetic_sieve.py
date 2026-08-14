import json

CONFIRMED_PRIME = "#008A7C"
UNRESOLVED_CANDIDATE = "#2457E6"
NEWLY_RESOLVED = "#D97706"
RESOLVED_COMPOSITE = "#E3E8EF"
NEUTRAL = "#FFFFFF"
INK = "#172033"
MUTED = "#667085"
BORDER = "#C7D0DD"


def build_kinetic_sieve_html(*, base_speed: float = 1.45, maximum_value: int = 2_000_000) -> str:
    """Build the self contained browser animation for Kinetic Sieve Lab."""
    if base_speed <= 0:
        raise ValueError("base_speed must be positive")
    if maximum_value < 100:
        raise ValueError("maximum_value must be at least 100")

    config = json.dumps({
        "baseSpeed": base_speed,
        "maximumValue": maximum_value,
        "colors": {
            "confirmed": CONFIRMED_PRIME,
            "candidate": UNRESOLVED_CANDIDATE,
            "newlyResolved": NEWLY_RESOLVED,
            "resolved": RESOLVED_COMPOSITE,
            "neutral": NEUTRAL,
            "ink": INK,
            "muted": MUTED,
            "border": BORDER,
        },
    })

    return f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; background:transparent; color:{INK}; }}
body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.shell {{ width:100%; border:1px solid #D7DEE8; border-radius:12px; background:#fff; overflow:hidden; }}
.top {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1px; background:#E6EBF2; border-bottom:1px solid #D7DEE8; }}
.metric {{ background:#fff; padding:12px 14px; min-height:70px; }}
.metric-label {{ color:#667085; font-size:12px; margin-bottom:5px; }}
.metric-value {{ color:#172033; font-size:21px; font-weight:650; line-height:1.1; }}
.stage {{ position:relative; background:#FBFCFE; }}
canvas {{ width:100%; height:520px; display:block; }}
.health {{ display:none; }}
.toolbar {{ min-height:48px; padding:8px 12px; display:flex; align-items:center; justify-content:space-between; gap:12px; border-top:1px solid #E6EBF2; background:#fff; color:#667085; font-size:12px; }}
.legend,.controls {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }}
.legend-item {{ display:inline-flex; align-items:center; gap:6px; white-space:nowrap; }}
.swatch {{ width:10px; height:10px; border-radius:3px; border:1px solid rgba(23,32,51,.14); }}
button {{ border:1px solid #C7D0DD; border-radius:7px; padding:6px 10px; background:#fff; color:#344054; cursor:pointer; font:inherit; }}
button:hover {{ background:#F8FAFC; }}
button.active {{ border-color:#98A2B3; background:#F2F4F7; font-weight:650; }}
.log {{ border-top:1px solid #E6EBF2; background:#fff; }}
.log-head {{ padding:10px 12px; display:flex; align-items:center; justify-content:space-between; gap:12px; }}
.log-title {{ font-size:13px; font-weight:650; color:#344054; }}
.log-sub {{ margin-top:2px; color:#667085; font-size:11px; }}
.log-table {{ width:100%; border-collapse:collapse; table-layout:fixed; font-size:11px; }}
.log-table th,.log-table td {{ padding:6px 10px; border-top:1px solid #F0F2F5; text-align:left; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.log-table th {{ color:#667085; font-weight:600; background:#FCFCFD; }}
.log-table td {{ color:#344054; }}
.error {{ display:none; padding:12px; background:#FEF3F2; color:#B42318; border-top:1px solid #FECDCA; font-size:12px; white-space:pre-wrap; }}
@media(max-width:850px) {{ .top{{grid-template-columns:repeat(2,minmax(0,1fr));}} .toolbar,.log-head{{align-items:flex-start;flex-direction:column;}} canvas{{height:500px;}} }}
</style>
</head>
<body>
<div class="shell">
  <div class="top">
    <div class="metric"><div class="metric-label">Frontier</div><div id="frontierValue" class="metric-value">1</div></div>
    <div class="metric"><div class="metric-label">Latest confirmed prime</div><div id="latestPrime" class="metric-value">None yet</div></div>
    <div class="metric"><div class="metric-label">Confirmed primes discovered</div><div id="primeCount" class="metric-value">0</div></div>
    <div class="metric"><div class="metric-label">Latest shared meeting</div><div id="latestMeeting" class="metric-value">None yet</div></div>
  </div>
  <div class="stage"><canvas id="stage"></canvas><div id="jsHealth" class="health" data-status="booting"></div></div>
  <div class="toolbar">
    <div class="legend">
      <span class="legend-item"><span class="swatch" style="background:{UNRESOLVED_CANDIDATE}"></span>Unresolved candidate</span>
      <span class="legend-item"><span class="swatch" style="background:{CONFIRMED_PRIME}"></span>Confirmed prime</span>
      <span class="legend-item"><span class="swatch" style="background:{NEWLY_RESOLVED}"></span>Newly resolved composite</span>
      <span class="legend-item"><span class="swatch" style="background:{RESOLVED_COMPOSITE}"></span>Resolved composite</span>
    </div>
    <div class="controls"><button id="pauseButton">Pause</button><button class="speed" data-speed="0.5">0.5×</button><button class="speed active" data-speed="1">1×</button><button class="speed" data-speed="2">2×</button></div>
  </div>
  <div class="log">
    <div class="log-head">
      <div><div class="log-title">Session event log</div><div class="log-sub">Records confirmed primes and shared prime meetings. Retention is bounded for long running sessions.</div></div>
      <div class="controls"><span id="logCount">0 events retained</span><button id="downloadLog">Download CSV</button></div>
    </div>
    <table class="log-table"><thead><tr><th style="width:15%">Integer</th><th style="width:22%">Event</th><th style="width:31%">Prime factors / prime</th><th>First eliminating prime</th></tr></thead><tbody id="logBody"><tr><td colspan="4">Waiting for the first event...</td></tr></tbody></table>
  </div>
  <div id="errorBox" class="error"></div>
</div>
<script>
(function() {{
'use strict';
const CONFIG = {config};
const colors = CONFIG.colors;
const canvas = document.getElementById('stage');
const ctx = canvas.getContext('2d');
const health = document.getElementById('jsHealth');
const errorBox = document.getElementById('errorBox');
const frontierValue = document.getElementById('frontierValue');
const latestPrime = document.getElementById('latestPrime');
const primeCount = document.getElementById('primeCount');
const latestMeeting = document.getElementById('latestMeeting');
const pauseButton = document.getElementById('pauseButton');
const speedButtons = Array.from(document.querySelectorAll('button.speed'));
const logBody = document.getElementById('logBody');
const logCount = document.getElementById('logCount');
const downloadLog = document.getElementById('downloadLog');

let cssWidth = 1200;
let cssHeight = 520;
let running = true;
let speedMultiplier = 1;
let simPosition = 1.55;
let processedThrough = 1;
let latestConfirmedPrime = null;
let primes = [];
let resolved = new Map();
let lastEvent = null;
let lastTimestamp = performance.now();
let cameraStart = 0;
let eventLog = [];
let logDirty = true;

const CELL_SIZE = 56;
const CELL_GAP = 9;
const PITCH = CELL_SIZE + CELL_GAP;
const LEFT_PAD = 30;
const RIGHT_PAD = 30;
const ROW_Y_RATIO = 0.73;
const EVENT_GLOW_SPAN = 0.58;
const CORE_TRACK_LIMIT = 31;
const DISPLAY_PRIME_LIMIT = 18;
const MEETING_HOLD_SPAN = 0.16;
const LOG_LIMIT = 10000;
const LOG_ROWS_VISIBLE = 7;
const ARC_SCALE = 0.78;

function fail(error) {{
  health.dataset.status = 'error';
  errorBox.style.display = 'block';
  errorBox.textContent = 'Kinetic Sieve browser error: ' + (error && error.stack ? error.stack : String(error));
  console.error(error);
}}

function resize() {{
  const rect = canvas.getBoundingClientRect();
  cssWidth = Math.max(320, rect.width || 1200);
  cssHeight = Math.max(440, rect.height || 520);
  const dpr = Math.max(1, Math.min(window.devicePixelRatio || 1, 2));
  canvas.width = Math.round(cssWidth * dpr);
  canvas.height = Math.round(cssHeight * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}}

function roundedRect(x,y,w,h,r) {{
  const rr = Math.min(r,w/2,h/2);
  ctx.beginPath(); ctx.moveTo(x+rr,y); ctx.arcTo(x+w,y,x+w,y+h,rr); ctx.arcTo(x+w,y+h,x,y+h,rr); ctx.arcTo(x,y+h,x,y,rr); ctx.arcTo(x,y,x+w,y,rr); ctx.closePath();
}}

function factorsFor(value) {{
  if (value < 2) return [];
  let remaining = value;
  const factors = [];
  for (const p of primes) {{
    if (p*p > remaining) break;
    if (remaining % p !== 0) continue;
    factors.push(p);
    while (remaining % p === 0) remaining /= p;
  }}
  if (remaining > 1 && factors.length > 0) factors.push(remaining);
  return factors;
}}

function addLog(event) {{
  if (event.kind !== 'prime' && event.kind !== 'meeting') return;
  eventLog.push({{ value:event.value, kind:event.kind === 'prime' ? 'Confirmed prime' : 'Shared meeting', factors:event.kind === 'prime' ? String(event.value) : event.factors.join(' · '), first:event.first == null ? '' : event.first }});
  if (eventLog.length > LOG_LIMIT) eventLog.splice(0, eventLog.length - LOG_LIMIT);
  logDirty = true;
}}

function processInteger(value) {{
  const factors = factorsFor(value);
  if (factors.length === 0) {{
    primes.push(value); latestConfirmedPrime = value;
    resolved.set(value, {{status:'prime',first:null,factors:[],eventAt:value}});
    lastEvent = {{value:value,kind:'prime',factors:[],first:null,eventAt:value}};
  }} else {{
    const first = factors[0];
    resolved.set(value, {{status:'composite',first:first,factors:factors,eventAt:value}});
    lastEvent = {{value:value,kind:factors.length >= 2 ? 'meeting' : 'composite',factors:factors,first:first,eventAt:value}};
  }}
  addLog(lastEvent);
  processedThrough = value;
  frontierValue.textContent = value.toLocaleString();
  latestPrime.textContent = latestConfirmedPrime == null ? 'None yet' : latestConfirmedPrime.toLocaleString();
  primeCount.textContent = primes.length.toLocaleString();
  if (lastEvent.kind === 'meeting') latestMeeting.textContent = lastEvent.factors.join(' · ') + ' at ' + value.toLocaleString();
}}

function ensureProcessed() {{
  const target = Math.floor(simPosition + 1e-9);
  while (processedThrough < target) processInteger(processedThrough + 1);
}}

function updateCamera(delta) {{
  const count = Math.max(10, Math.floor((cssWidth - LEFT_PAD - RIGHT_PAD) / PITCH));
  const anchor = Math.max(5, Math.floor(count * 0.38));
  const target = Math.max(0, simPosition - anchor);
  cameraStart += (target - cameraStart) * Math.min(1, delta * 2.2);
}}

function geometry() {{
  const count = Math.max(10, Math.floor((cssWidth - LEFT_PAD - RIGHT_PAD) / PITCH));
  return {{count:count, smoothStart:cameraStart, first:Math.floor(cameraStart), last:Math.floor(cameraStart)+count+2}};
}}
function worldX(value,g) {{ return LEFT_PAD + (value-g.smoothStart)*PITCH + CELL_SIZE/2; }}
function cellState(value) {{ if(value<2)return {{status:'neutral'}}; if(value>processedThrough)return {{status:'candidate'}}; return resolved.get(value)||{{status:'candidate'}}; }}
function numberFont(value) {{ const n=value.toLocaleString().length; return n<=3?16:n<=5?14:n<=7?12:10; }}

function drawCell(value,g,rowY) {{
  const cx=worldX(value,g), x=cx-CELL_SIZE/2, y=rowY-CELL_SIZE/2, state=cellState(value);
  let fill=colors.candidate, text='#fff', border='rgba(23,32,51,.16)';
  if(state.status==='neutral'){{fill=colors.neutral;text=colors.ink;border=colors.border;}}
  else if(state.status==='prime'){{fill=colors.confirmed;}}
  else if(state.status==='composite'){{const age=simPosition-state.eventAt;fill=age<=EVENT_GLOW_SPAN?colors.newlyResolved:colors.resolved;text=age<=EVENT_GLOW_SPAN?'#fff':colors.ink;}}
  roundedRect(x,y,CELL_SIZE,CELL_SIZE,9);ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle=border;ctx.lineWidth=1;ctx.stroke();
  ctx.fillStyle=text;ctx.font='650 '+numberFont(value)+'px Inter, system-ui, sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(value.toLocaleString(),cx,rowY+.5);
}}

function primeSegment(prime) {{
  const q=Math.max(1,Math.floor(simPosition/prime));
  const previous=q*prime, next=previous+prime;
  const phase=Math.max(0,Math.min(1,(simPosition-previous)/prime));
  return {{previous:previous,next:next,phase:phase}};
}}
function arcHeight(prime) {{ const span=prime*PITCH; return Math.max(48,Math.min(cssHeight*.58,(span/Math.PI)*ARC_SCALE)); }}
function shouldDrawPrime(prime,g) {{
  if(prime>simPosition+1e-9)return false;
  if(simPosition-prime<.9)return true;
  const s=primeSegment(prime);
  return s.previous<=g.last+2 && s.next>=g.first-2 && (prime<=CORE_TRACK_LIMIT || s.next<=g.last+2);
}}
function chooseDisplayPrimes(g) {{ return primes.filter(function(p){{return shouldDrawPrime(p,g);}}).slice(0,DISPLAY_PRIME_LIMIT); }}

function drawArc(prime,g,rowY) {{
  const s=primeSegment(prime), h=arcHeight(prime), samples=40;
  ctx.save();ctx.beginPath();
  for(let i=0;i<=samples;i++){{const t=i/samples, value=s.previous+prime*t, x=worldX(value,g), y=rowY-h*Math.sin(Math.PI*t);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}}
  ctx.strokeStyle='rgba(0,138,124,.20)';ctx.lineWidth=1.4;ctx.stroke();ctx.restore();
}}
function drawPrimeToken(prime,g,rowY) {{
  const s=primeSegment(prime), h=arcHeight(prime), phase=s.phase;
  let x=worldX(s.previous+prime*phase,g), y=rowY-h*Math.sin(Math.PI*phase);
  if(lastEvent && lastEvent.kind==='meeting' && lastEvent.factors.indexOf(prime)>=0 && simPosition-lastEvent.eventAt>=0 && simPosition-lastEvent.eventAt<=MEETING_HOLD_SPAN){{x=worldX(lastEvent.value,g);y=rowY;}}
  const born=Math.max(0,1-(simPosition-prime)/.7), size=35*(1+.18*born);
  ctx.save();ctx.shadowColor='rgba(0,138,124,.22)';ctx.shadowBlur=8;roundedRect(x-size/2,y-size/2,size,size,8);ctx.fillStyle=colors.confirmed;ctx.fill();ctx.shadowBlur=0;ctx.strokeStyle='rgba(255,255,255,.55)';ctx.stroke();
  ctx.fillStyle='#fff';ctx.font='700 12px Inter, system-ui, sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(String(prime),x,y+.5);ctx.restore();
}}

function drawFrontier(g,rowY) {{ const x=worldX(simPosition,g);ctx.save();ctx.strokeStyle='rgba(36,87,230,.28)';ctx.setLineDash([4,5]);ctx.beginPath();ctx.moveTo(x,40);ctx.lineTo(x,rowY+CELL_SIZE*.9);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=colors.muted;ctx.font='600 11px Inter, system-ui, sans-serif';ctx.textAlign='center';ctx.fillText('discovery frontier',x,27);ctx.restore(); }}
function drawMeeting(g,rowY) {{ if(!lastEvent||lastEvent.kind!=='meeting')return;const age=simPosition-lastEvent.eventAt;if(age<0||age>.72)return;const x=worldX(lastEvent.value,g),progress=Math.min(1,age/.72);ctx.save();ctx.globalAlpha=.72*(1-progress);ctx.strokeStyle=colors.confirmed;ctx.lineWidth=3;ctx.beginPath();ctx.arc(x,rowY,30+30*progress,0,Math.PI*2);ctx.stroke();ctx.restore();ctx.fillStyle=colors.ink;ctx.font='650 13px Inter, system-ui, sans-serif';ctx.textAlign='center';ctx.fillText(lastEvent.factors.join(' · ')+' meet at '+lastEvent.value.toLocaleString(),x,Math.max(55,rowY-285)); }}
function drawPrimeDiscovery(g,rowY) {{ if(!lastEvent||lastEvent.kind!=='prime')return;const age=simPosition-lastEvent.eventAt;if(age<0||age>.8)return;const x=worldX(lastEvent.value,g),progress=Math.min(1,age/.8);ctx.save();ctx.globalAlpha=1-.7*progress;ctx.fillStyle=colors.confirmed;ctx.font='650 12px Inter, system-ui, sans-serif';ctx.textAlign='center';ctx.fillText('Prime '+lastEvent.value.toLocaleString()+' confirmed',x,rowY-64-34*progress);ctx.restore(); }}
function drawStatus() {{ if(!lastEvent)return;let text='';if(lastEvent.kind==='prime')text=lastEvent.value.toLocaleString()+' reached the frontier with no earlier prime trajectory landing on it.';else if(lastEvent.kind==='meeting')text=lastEvent.factors.join(', ')+' arrive together. '+lastEvent.first+' remains the first eliminating prime.';else text='Prime '+lastEvent.first+' resolves '+lastEvent.value.toLocaleString()+' as composite.';ctx.fillStyle=colors.muted;ctx.font='12px Inter, system-ui, sans-serif';ctx.textAlign='left';ctx.fillText(text,LEFT_PAD,cssHeight-20); }}

function refreshLog() {{
  if(!logDirty)return;
  const rows=eventLog.slice(-LOG_ROWS_VISIBLE).reverse();
  if(rows.length===0) logBody.innerHTML='<tr><td colspan="4">Waiting for the first event...</td></tr>';
  else logBody.innerHTML=rows.map(function(row){{return '<tr><td>'+row.value.toLocaleString()+'</td><td>'+row.kind+'</td><td>'+row.factors+'</td><td>'+(row.first||'—')+'</td></tr>';}}).join('');
  logCount.textContent=eventLog.length.toLocaleString()+' events retained';
  logDirty=false;
}}
function prune(g) {{ const cutoff=g.first-8;if(cutoff<=0)return;for(const key of resolved.keys()){{if(key>=cutoff)break;resolved.delete(key);}} }}

function render() {{
  ctx.clearRect(0,0,cssWidth,cssHeight);ctx.fillStyle='#FBFCFE';ctx.fillRect(0,0,cssWidth,cssHeight);
  const g=geometry(),rowY=cssHeight*ROW_Y_RATIO;
  drawFrontier(g,rowY);
  for(let value=Math.max(0,g.first-1);value<=g.last+2;value++)drawCell(value,g,rowY);
  const visiblePrimes=chooseDisplayPrimes(g);
  visiblePrimes.forEach(function(p){{drawArc(p,g,rowY);}});
  visiblePrimes.forEach(function(p){{drawPrimeToken(p,g,rowY);}});
  drawMeeting(g,rowY);drawPrimeDiscovery(g,rowY);drawStatus();refreshLog();prune(g);
}}

function frame(timestamp) {{
  try {{
    const raw=Math.max(0,(timestamp-lastTimestamp)/1000), delta=Math.min(raw,.08);lastTimestamp=timestamp;
    if(running && simPosition<CONFIG.maximumValue){{simPosition=Math.min(CONFIG.maximumValue,simPosition+CONFIG.baseSpeed*speedMultiplier*delta);ensureProcessed();}}
    updateCamera(delta);render();health.dataset.status='running';requestAnimationFrame(frame);
  }} catch(error) {{ fail(error); }}
}}

function csvEscape(value) {{ return '"'+String(value == null ? '' : value).replace(/"/g,'""')+'"'; }}
pauseButton.addEventListener('click',function(){{running=!running;pauseButton.textContent=running?'Pause':'Resume';}});
speedButtons.forEach(function(button){{button.addEventListener('click',function(){{speedMultiplier=Number(button.dataset.speed);speedButtons.forEach(function(item){{item.classList.remove('active');}});button.classList.add('active');}});}});
downloadLog.addEventListener('click',function(){{
  const lines=['integer,event,prime_factors_or_prime,first_eliminating_prime'];
  eventLog.forEach(function(row){{lines.push([row.value,row.kind,row.factors,row.first].map(csvEscape).join(','));}});
  const blob=new Blob([lines.join('\\n')],{{type:'text/csv;charset=utf-8'}}),url=URL.createObjectURL(blob),link=document.createElement('a');
  link.href=url;link.download='prime-lab-kinetic-events-through-'+processedThrough+'.csv';document.body.appendChild(link);link.click();link.remove();setTimeout(function(){{URL.revokeObjectURL(url);}},1000);
}});

try {{ resize(); window.addEventListener('resize',resize); health.dataset.status='ready'; requestAnimationFrame(frame); }} catch(error) {{ fail(error); }}
}})();
</script>
</body>
</html>'''
