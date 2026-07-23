#!/usr/bin/env python3
"""scrape the public contribution calendar (no token, no GraphQL) and
derive stats used by render_heatmap_svg.py.

Usage: python scripts/fetch_contributions.py [username]
Output: data/contributions.json
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "Drago-03"
OUT_PATH = Path("data/contributions.json")


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_count(tooltip_text: str) -> int:
    text = tooltip_text.strip()
    if text.lower().startswith("no contributions"):
        return 0
    m = re.match(r"([\d,]+)\s+contribution", text)
    return int(m.group(1).replace(",", "")) if m else 0


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    tooltips = {}
    for tip in soup.select("tool-tip[for]"):
        tooltips[tip["for"]] = tip.get_text()

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        td_date = td.get("data-date")
        if not td_date:
            continue
        level = int(td.get("data-level", 0))
        count = parse_count(tooltips.get(td.get("id"), ""))
        days.append({"date": td_date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def parse_total(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find(id="js-contribution-activity-description")
    if not heading:
        return 0
    m = re.search(r"([\d,]+)\s+contribution", heading.get_text(" ", strip=True))
    return int(m.group(1).replace(",", "")) if m else 0


def compute_streaks(days: list[dict]) -> tuple[int, int]:
    longest = current_run = 0
    for d in days:
        if d["count"] > 0:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 0

    i = len(days) - 1
    if days and days[i]["count"] == 0:
        i -= 1  # today may not have contributions yet; don't break the streak on it
    current = 0
    while i >= 0 and days[i]["count"] > 0:
        current += 1
        i -= 1
    return current, longest


def monthly_totals(days: list[dict]) -> dict:
    totals: dict[str, int] = {}
    for d in days:
        month = d["date"][:7]
        totals[month] = totals.get(month, 0) + d["count"]
    return dict(sorted(totals.items()))


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    html = fetch_html(username)
    days = parse_days(html)
    if not days:
        raise SystemExit("no contribution cells parsed — GitHub markup may have changed")

    total = parse_total(html) or sum(d["count"] for d in days)
    current_streak, longest_streak = compute_streaks(days)
    best_day = max(days, key=lambda d: d["count"])

    payload = {
        "username": username,
        "generated_at": date.today().isoformat(),
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": monthly_totals(days),
        "days": days,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT_PATH} ({len(days)} days, {total} contributions)")


if __name__ == "__main__":
    main()
