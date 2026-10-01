#!/usr/bin/env python3
import hashlib
import html
import json
import math
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

USERNAME = os.getenv("GITHUB_USERNAME", "Luiz-Gabriel01")
TOKEN = os.environ["GITHUB_TOKEN"]
OUTPUT = Path("assets/contribution-system.svg")
TZ = ZoneInfo("America/Recife")


def github_graphql(query, variables):
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Luiz-Gabriel01-contribution-system",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], ensure_ascii=False))
    return result["data"]


def get_contributions():
    now_local = datetime.now(TZ)
    now_utc = now_local.astimezone(timezone.utc)
    start_utc = now_utc - timedelta(days=364)

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
                color
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "login": USERNAME,
        "from": start_utc.isoformat().replace("+00:00", "Z"),
        "to": now_utc.isoformat().replace("+00:00", "Z"),
    }
    data = github_graphql(query, variables)
    user = data.get("user")
    if not user:
        raise RuntimeError(f"GitHub user {USERNAME} not found")

    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in calendar["weeks"]:
        for item in week["contributionDays"]:
            days.append({
                "date": datetime.strptime(item["date"], "%Y-%m-%d").date(),
                "count": int(item["contributionCount"]),
            })
    days.sort(key=lambda d: d["date"])
    return now_local.date(), days


def metric_data(today, days):
    by_date = {d["date"]: d["count"] for d in days}
    today_count = by_date.get(today, 0)

    week_start = today - timedelta(days=today.weekday())
    week_total = sum(by_date.get(week_start + timedelta(days=i), 0) for i in range((today - week_start).days + 1))

    month_start = today.replace(day=1)
    month_total = 0
    cursor = month_start
    while cursor <= today:
        month_total += by_date.get(cursor, 0)
        cursor += timedelta(days=1)

    streak_cursor = today
    if by_date.get(streak_cursor, 0) == 0:
        streak_cursor -= timedelta(days=1)
    streak = 0
    while by_date.get(streak_cursor, 0) > 0:
        streak += 1
        streak_cursor -= timedelta(days=1)

    last_30 = []
    for offset in range(29, -1, -1):
        date = today - timedelta(days=offset)
        last_30.append((date, by_date.get(date, 0)))

    last_84 = []
    for offset in range(83, -1, -1):
        date = today - timedelta(days=offset)
        last_84.append((date, by_date.get(date, 0)))

    return {
        "today": today_count,
        "week": week_total,
        "month": month_total,
        "streak": streak,
        "last_30": last_30,
        "last_84": last_84,
    }


def esc(text):
    return html.escape(str(text), quote=True)


def star_position(date_obj, index):
    digest = hashlib.sha256(date_obj.isoformat().encode()).digest()
    ring = index % 4
    radii = (78, 128, 178, 228)
    radius = radii[ring] + (digest[0] % 13) - 6
    angle = math.radians((index * 137.508 + digest[1]) % 360)
    x = 600 + math.cos(angle) * radius
    y = 423 + math.sin(angle) * radius * 0.50
    return x, y


def render_svg(today, metrics):
    width, height = 1200, 820
    today_count = metrics["today"]
    status = "ORBIT ACTIVE" if today_count > 0 else "AWAITING SIGNAL"
    status_sub = f"{today_count} contribuição" + ("" if today_count == 1 else "ões") + " hoje"

    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Contribution System de Luiz Gabriel</title>
<desc id="desc">Painel galáctico atualizado automaticamente com status diário, streak, contribuições da semana, galáxia de contribuições e atividade mensal.</desc>
<defs>
  <radialGradient id="bg" cx="50%" cy="42%" r="78%">
    <stop offset="0" stop-color="#151108"/>
    <stop offset="0.38" stop-color="#090a0d"/>
    <stop offset="1" stop-color="#030406"/>
  </radialGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fff4b0"/>
    <stop offset="0.38" stop-color="#ffd700"/>
    <stop offset="1" stop-color="#8a6500"/>
  </linearGradient>
  <linearGradient id="bar" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0" stop-color="#5a4300"/>
    <stop offset="1" stop-color="#ffd700"/>
  </linearGradient>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="soft" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="14"/>
  </filter>
</defs>
<rect width="1200" height="820" rx="28" fill="url(#bg)"/>
<rect x="1" y="1" width="1198" height="818" rx="27" fill="none" stroke="#ffd700" stroke-opacity="0.14"/>

<!-- Ambient stars -->
<g fill="#ffd700" opacity="0.28">
  <circle cx="70" cy="80" r="1"/><circle cx="180" cy="54" r="1.3"/><circle cx="310" cy="93" r="0.8"/>
  <circle cx="454" cy="58" r="1"/><circle cx="738" cy="74" r="1.1"/><circle cx="884" cy="46" r="0.9"/>
  <circle cx="1032" cy="87" r="1.3"/><circle cx="1130" cy="56" r="0.8"/>
  <circle cx="96" cy="468" r="1.1"/><circle cx="1082" cy="488" r="1"/>
</g>

<text x="56" y="54" fill="#ffd700" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="20" font-weight="700" letter-spacing="2.5">&gt; CONTRIBUTION_SYSTEM</text>
<text x="56" y="79" fill="#666d78" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="11" letter-spacing="1.2">LIVE GITHUB TELEMETRY // {esc(today.strftime('%d.%m.%Y'))}</text>

<!-- Metric cards -->
<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
  <rect x="56" y="108" width="260" height="112" rx="16" fill="#0d0f13" stroke="#ffd700" stroke-opacity="0.22"/>
  <text x="78" y="139" fill="#727986" font-size="11" letter-spacing="1.4">DAILY STATUS</text>
  <text x="78" y="174" fill="#ffd700" font-size="23" font-weight="700">{esc(status)}</text>
  <text x="78" y="199" fill="#b7bdc8" font-size="12">{esc(status_sub)}</text>
  <circle cx="290" cy="134" r="4" fill="#ffd700" filter="url(#glow)">
    <animate attributeName="opacity" values="0.35;1;0.35" dur="2.2s" repeatCount="indefinite"/>
  </circle>

  <rect x="332" y="108" width="236" height="112" rx="16" fill="#0d0f13" stroke="#ffd700" stroke-opacity="0.22"/>
  <text x="354" y="139" fill="#727986" font-size="11" letter-spacing="1.4">CURRENT STREAK</text>
  <text x="354" y="181" fill="#f4f5f7" font-size="34" font-weight="700">{metrics['streak']}</text>
  <text x="414" y="181" fill="#ffd700" font-size="13">DAYS</text>
  <text x="354" y="201" fill="#777f8b" font-size="11">sequência ativa</text>

  <rect x="584" y="108" width="260" height="112" rx="16" fill="#0d0f13" stroke="#ffd700" stroke-opacity="0.22"/>
  <text x="606" y="139" fill="#727986" font-size="11" letter-spacing="1.4">THIS WEEK</text>
  <text x="606" y="181" fill="#f4f5f7" font-size="34" font-weight="700">{metrics['week']}</text>
  <text x="680" y="181" fill="#ffd700" font-size="13">CONTRIB.</text>
  <text x="606" y="201" fill="#777f8b" font-size="11">segunda → hoje</text>

  <rect x="860" y="108" width="284" height="112" rx="16" fill="#0d0f13" stroke="#ffd700" stroke-opacity="0.22"/>
  <text x="882" y="139" fill="#727986" font-size="11" letter-spacing="1.4">CURRENT MONTH</text>
  <text x="882" y="181" fill="#f4f5f7" font-size="34" font-weight="700">{metrics['month']}</text>
  <text x="956" y="181" fill="#ffd700" font-size="13">CONTRIB.</text>
  <text x="882" y="201" fill="#777f8b" font-size="11">atividade no mês</text>
</g>

<!-- Contribution galaxy -->
<text x="56" y="266" fill="#f1f3f5" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14" font-weight="700" letter-spacing="1.5">04 // CONTRIBUTION GALAXY</text>
<text x="56" y="287" fill="#666d78" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10">cada estrela representa um dos últimos 84 dias • brilho = intensidade</text>

<ellipse cx="600" cy="423" rx="240" ry="120" fill="#ffd700" opacity="0.025" filter="url(#soft)"/>
<g fill="none" stroke="#ffd700" stroke-opacity="0.10">
  <ellipse cx="600" cy="423" rx="78" ry="39"/>
  <ellipse cx="600" cy="423" rx="128" ry="64"/>
  <ellipse cx="600" cy="423" rx="178" ry="89"/>
  <ellipse cx="600" cy="423" rx="228" ry="114"/>
</g>
<circle cx="600" cy="423" r="24" fill="#ffd700" opacity="0.10" filter="url(#soft)"/>
<circle cx="600" cy="423" r="9" fill="url(#gold)" filter="url(#glow)"/>
<circle cx="600" cy="423" r="3" fill="#fff7c9"/>
''']

    max_84 = max((count for _, count in metrics["last_84"]), default=1) or 1
    for idx, (date_obj, count) in enumerate(metrics["last_84"]):
        x, y = star_position(date_obj, idx)
        intensity = min(count / max_84, 1.0)
        if count == 0:
            radius = 1.05
            fill = "#303640"
            opacity = 0.50
            glow = ""
        else:
            radius = 1.8 + intensity * 4.3
            fill = "#ffd700" if intensity > 0.45 else "#b98a00"
            opacity = 0.62 + intensity * 0.38
            glow = ' filter="url(#glow)"' if intensity > 0.35 else ""
        title = f"{date_obj.isoformat()}: {count} contribuições"
        extra = ""
        if date_obj == today:
            extra = '<animate attributeName="r" values="3;6;3" dur="2s" repeatCount="indefinite"/>'
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.2f}" fill="{fill}" opacity="{opacity:.2f}"{glow}>'
            f'<title>{esc(title)}</title>{extra}</circle>'
        )

    parts.append('''
<text x="600" y="566" text-anchor="middle" fill="#6f7680" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10" letter-spacing="1.2">84-DAY ORBIT // LIVE CONTRIBUTION MAP</text>

<!-- Monthly activity -->
<text x="56" y="624" fill="#f1f3f5" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14" font-weight="700" letter-spacing="1.5">05 // MONTHLY ACTIVITY PANEL</text>
<text x="56" y="645" fill="#666d78" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10">últimos 30 dias • altura da barra = contribuições no dia</text>
<line x1="56" y1="760" x2="1144" y2="760" stroke="#2a2f36"/>
''')

    max_30 = max((count for _, count in metrics["last_30"]), default=1) or 1
    start_x = 61
    base_y = 758
    bar_w = 22
    gap = 14
    for idx, (date_obj, count) in enumerate(metrics["last_30"]):
        x = start_x + idx * (bar_w + gap)
        h = 5 if count == 0 else 10 + (count / max_30) * 72
        y = base_y - h
        opacity = 0.22 if count == 0 else 0.45 + 0.55 * (count / max_30)
        stroke = '#fff2a8' if date_obj == today else '#ffd700'
        parts.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" rx="5" fill="url(#bar)" opacity="{opacity:.2f}" stroke="{stroke}" stroke-opacity="0.28">'
            f'<title>{esc(date_obj.strftime("%d/%m"))}: {count} contribuições</title></rect>'
        )
        if idx % 5 == 0 or idx == 29:
            parts.append(
                f'<text x="{x + bar_w/2:.1f}" y="785" text-anchor="middle" fill="#606773" '
                f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9">{date_obj.strftime("%d/%m")}</text>'
            )

    parts.append('''
<text x="1144" y="803" text-anchor="end" fill="#4d535d" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9" letter-spacing="1">AUTO-UPDATED BY GITHUB ACTIONS</text>
</svg>''')
    return "".join(parts)


def main():
    today, days = get_contributions()
    metrics = metric_data(today, days)
    svg = render_svg(today, metrics)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(
        f"Generated {OUTPUT} | today={metrics['today']} streak={metrics['streak']} "
        f"week={metrics['week']} month={metrics['month']}"
    )


if __name__ == "__main__":
    main()
