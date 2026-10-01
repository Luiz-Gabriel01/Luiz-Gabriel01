#!/usr/bin/env python3
import hashlib, html, json, math, os, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

USERNAME = os.getenv('GITHUB_USERNAME', 'Luiz-Gabriel01')
TOKEN = os.environ['GITHUB_TOKEN']
OUTPUT = Path('assets/contribution-system.svg')
TZ = ZoneInfo('America/Recife')
C = {
    'bg0':'#121830','bg1':'#090B17','bg2':'#02040B','panel':'#0B1020','stroke':'#39C6FF','title':'#8EDBFF',
    'text':'#E8F3FF','muted':'#93A1C6','subtle':'#667594','violet':'#6C63FF','cyan':'#39C6FF',
    'dim':'#2B334B','low':'#4BC8FF','high':'#A78BFF','core':'#CFF4FF','tip':'#C6B7FF'
}

def gql(q, v):
    req = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query':q,'variables':v}).encode(), headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json','User-Agent':f'{USERNAME}-contribution-system'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r: data = json.load(r)
    if data.get('errors'): raise RuntimeError(json.dumps(data['errors'], ensure_ascii=False))
    return data['data']

def contributions():
    now = datetime.now(TZ); now_utc = now.astimezone(timezone.utc); start = now_utc - timedelta(days=364)
    q = '''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{contributionCount date}}}}}}'''
    v = {'login':USERNAME,'from':start.isoformat().replace('+00:00','Z'),'to':now_utc.isoformat().replace('+00:00','Z')}
    weeks = gql(q,v)['user']['contributionsCollection']['contributionCalendar']['weeks']
    days=[]
    for w in weeks:
        for d in w['contributionDays']:
            days.append((datetime.strptime(d['date'],'%Y-%m-%d').date(), int(d['contributionCount'])))
    days.sort(); return now.date(), days

def metrics(today, days):
    m = dict(days); week_start = today - timedelta(days=today.weekday())
    week = sum(m.get(week_start + timedelta(days=i), 0) for i in range((today - week_start).days + 1))
    cur = today.replace(day=1); month = 0
    while cur <= today: month += m.get(cur,0); cur += timedelta(days=1)
    cur = today if m.get(today,0) > 0 else today - timedelta(days=1); streak = 0
    while m.get(cur,0) > 0: streak += 1; cur -= timedelta(days=1)
    last30=[(today-timedelta(days=o), m.get(today-timedelta(days=o),0)) for o in range(29,-1,-1)]
    last84=[(today-timedelta(days=o), m.get(today-timedelta(days=o),0)) for o in range(83,-1,-1)]
    return {'today':m.get(today,0),'week':week,'month':month,'streak':streak,'last30':last30,'last84':last84}

def esc(x): return html.escape(str(x), quote=True)
def pos(d, i):
    h = hashlib.sha256(d.isoformat().encode()).digest(); ring = i % 4; radius = (78,128,178,228)[ring] + (h[0] % 13) - 6; a = math.radians((i*137.508 + h[1]) % 360)
    return 600 + math.cos(a)*radius, 423 + math.sin(a)*radius*0.50

def plural(n): return f'{n} contribuição' if n == 1 else f'{n} contribuições'

def render(today, m):
    status = 'ORBIT ACTIVE' if m['today'] > 0 else 'AWAITING SIGNAL'
    p=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="820" viewBox="0 0 1200 820" role="img" aria-labelledby="title desc">
<title id="title">Contribution System de Luiz Gabriel</title><desc id="desc">Painel espacial atualizado automaticamente com status diário, streak, contribuições da semana, galáxia de contribuições e atividade mensal.</desc>
<defs><radialGradient id="bg" cx="50%" cy="42%" r="78%"><stop offset="0" stop-color="{C['bg0']}"/><stop offset=".40" stop-color="{C['bg1']}"/><stop offset="1" stop-color="{C['bg2']}"/></radialGradient><linearGradient id="nebula" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C['cyan']}"/><stop offset=".5" stop-color="{C['violet']}"/><stop offset="1" stop-color="#A78BFF"/></linearGradient><linearGradient id="bar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{C['cyan']}"/><stop offset="1" stop-color="#7C5CFF"/></linearGradient><filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><filter id="soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="14"/></filter></defs>
<rect width="1200" height="820" rx="28" fill="url(#bg)"/><rect x="1" y="1" width="1198" height="818" rx="27" fill="none" stroke="{C['cyan']}" stroke-opacity=".14"/>
<g fill="{C['core']}" opacity=".45"><circle cx="70" cy="80" r="1"/><circle cx="180" cy="54" r="1.3"/><circle cx="310" cy="93" r=".8"/><circle cx="454" cy="58" r="1"/><circle cx="738" cy="74" r="1.1"/><circle cx="884" cy="46" r=".9"/><circle cx="1032" cy="87" r="1.3"/><circle cx="1130" cy="56" r=".8"/><circle cx="96" cy="468" r="1.1"/><circle cx="1082" cy="488" r="1"/></g>
<text x="56" y="54" fill="{C['title']}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="20" font-weight="700" letter-spacing="2.5">&gt; CONTRIBUTION_SYSTEM</text><text x="56" y="79" fill="{C['subtle']}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="11" letter-spacing="1.2">LIVE SPACE TELEMETRY // {today.strftime('%d.%m.%Y')}</text>
<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"><rect x="56" y="108" width="260" height="112" rx="16" fill="{C['panel']}" stroke="{C['cyan']}" stroke-opacity=".18"/><text x="78" y="139" fill="{C['subtle']}" font-size="11" letter-spacing="1.4">DAILY STATUS</text><text x="78" y="174" fill="{C['title']}" font-size="23" font-weight="700">{esc(status)}</text><text x="78" y="199" fill="{C['muted']}" font-size="12">{esc(plural(m['today']) + ' hoje')}</text><circle cx="290" cy="134" r="4" fill="{C['cyan']}" filter="url(#glow)"><animate attributeName="opacity" values="0.35;1;0.35" dur="2.2s" repeatCount="indefinite"/></circle>
<rect x="332" y="108" width="236" height="112" rx="16" fill="{C['panel']}" stroke="{C['cyan']}" stroke-opacity=".18"/><text x="354" y="139" fill="{C['subtle']}" font-size="11" letter-spacing="1.4">CURRENT STREAK</text><text x="354" y="181" fill="{C['text']}" font-size="34" font-weight="700">{m['streak']}</text><text x="414" y="181" fill="{C['cyan']}" font-size="13">DAYS</text><text x="354" y="201" fill="{C['subtle']}" font-size="11">sequência ativa</text>
<rect x="584" y="108" width="260" height="112" rx="16" fill="{C['panel']}" stroke="{C['cyan']}" stroke-opacity=".18"/><text x="606" y="139" fill="{C['subtle']}" font-size="11" letter-spacing="1.4">THIS WEEK</text><text x="606" y="181" fill="{C['text']}" font-size="34" font-weight="700">{m['week']}</text><text x="680" y="181" fill="{C['cyan']}" font-size="13">CONTRIB.</text><text x="606" y="201" fill="{C['subtle']}" font-size="11">segunda → hoje</text>
<rect x="860" y="108" width="284" height="112" rx="16" fill="{C['panel']}" stroke="{C['cyan']}" stroke-opacity=".18"/><text x="882" y="139" fill="{C['subtle']}" font-size="11" letter-spacing="1.4">CURRENT MONTH</text><text x="882" y="181" fill="{C['text']}" font-size="34" font-weight="700">{m['month']}</text><text x="956" y="181" fill="{C['cyan']}" font-size="13">CONTRIB.</text><text x="882" y="201" fill="{C['subtle']}" font-size="11">atividade no mês</text></g>
<text x="56" y="266" fill="{C['text']}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14" font-weight="700" letter-spacing="1.5">04 // CONTRIBUTION GALAXY</text><text x="56" y="287" fill="{C['subtle']}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10">cada estrela representa um dos últimos 84 dias • brilho = intensidade</text>
<ellipse cx="600" cy="423" rx="240" ry="120" fill="{C['violet']}" opacity=".035" filter="url(#soft)"/><g fill="none" stroke="{C['cyan']}" stroke-opacity=".12"><ellipse cx="600" cy="423" rx="78" ry="39"/><ellipse cx="600" cy="423" rx="128" ry="64"/><ellipse cx="600" cy="423" rx="178" ry="89"/><ellipse cx="600" cy="423" rx="228" ry="114"/></g><circle cx="600" cy="423" r="28" fill="{C['violet']}" opacity=".16" filter="url(#soft)"/><circle cx="600" cy="423" r="11" fill="url(#nebula)" filter="url(#glow)"/><circle cx="600" cy="423" r="4" fill="{C['core']}"/>''']
    mx84=max((c for _,c in m['last84']), default=1) or 1
    for i,(d,c) in enumerate(m['last84']):
        x,y=pos(d,i); t=min(c/mx84,1.0) if mx84 else 0
        if c==0: r,fill,op,glow=1.1,C['dim'],.55,''
        else: r,fill,op,glow=1.8+t*4.6,(C['high'] if t>.55 else C['low']),.70+t*.30,(' filter="url(#glow)"' if t>.25 else '')
        extra = '<animate attributeName="r" values="3;6;3" dur="2s" repeatCount="indefinite"/>' if d == today and c > 0 else ''
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{fill}" opacity="{op:.2f}"{glow}><title>{esc(d.isoformat()+": "+str(c)+" contribuições")}</title>{extra}</circle>')
    p.append(f'<text x="600" y="566" text-anchor="middle" fill="{C["subtle"]}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10" letter-spacing="1.2">84-DAY ORBIT // LIVE CONTRIBUTION MAP</text><text x="56" y="624" fill="{C["text"]}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14" font-weight="700" letter-spacing="1.5">05 // MONTHLY ACTIVITY PANEL</text><text x="56" y="645" fill="{C["subtle"]}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10">últimos 30 dias • altura da barra = contribuições no dia</text><line x1="56" y1="760" x2="1144" y2="760" stroke="#25304A"/>')
    mx30=max((c for _,c in m['last30']), default=1) or 1
    for i,(d,c) in enumerate(m['last30']):
        x=61+i*36; h=8 if c==0 else 10+(c/mx30)*88; y=758-h; fill='url(#bar)' if c>0 else '#1A2236'; op='1' if c>0 else '.65'
        p.append(f'<rect x="{x}" y="{y:.1f}" width="22" height="{h:.1f}" rx="7" fill="{fill}" opacity="{op}"/>')
        if c>0: p.append(f'<circle cx="{x+11:.1f}" cy="{y+3:.1f}" r="2.3" fill="{C["tip"]}" opacity=".9"/>')
        if i%5==0: p.append(f'<text x="{x+11:.1f}" y="782" text-anchor="middle" fill="{C["subtle"]}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="8">{d.strftime("%d/%m")}</text>')
    p.append(f'<text x="1142" y="782" text-anchor="end" fill="{C["subtle"]}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="8">30 DAYS WINDOW</text></svg>')
    return ''.join(p)

def main():
    today, days = contributions(); OUTPUT.parent.mkdir(parents=True, exist_ok=True); OUTPUT.write_text(render(today, metrics(today, days)), encoding='utf-8')

if __name__ == '__main__': main()
