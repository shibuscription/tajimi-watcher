#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import datetime
import json
import os

def get_target_date():
    now = datetime.datetime.now()
    jst_hour = now.hour + 9  # Actions は UTC → JST

    if jst_hour >= 24:
        jst_hour -= 24

    if jst_hour < 3:
        # 深夜なら前日
        target_date = now - datetime.timedelta(days=1)
    else:
        target_date = now

    return target_date.strftime("%m%d"), target_date.strftime("%Y-%m-%d")

def scrape_temperature(date_str):
    url = f"http://www.data.jma.go.jp/obd/stats/data/mdrr/tem_rct/alltable/mxtemsad{date_str}.html"
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    # 時刻情報
    h1 = soup.find('h1').text
    time = h1.replace("日最高気温一覧表（", "").replace("）", "")

    entries = []
    rows = soup.select('div#main table.data2_s tr.mtx')
    for row in rows:
        tds = row.find_all('td')
        if len(tds) < 5:
            continue
        pref = tds[0].text.strip()
        place = tds[2].text.strip().replace("*", "").split("（")[0]
        temp = tds[3].text.strip().replace("×", "")
        rectime = tds[4].text.strip()
        try:
            temp_float = float(temp)
        except ValueError:
            continue
        entries.append({
            "pref": pref,
            "place": place,
            "temp": temp_float,
            "time": rectime
        })

    # ソート
    entries.sort(key=lambda x: x["temp"], reverse=True)

    # ランク付け
    for i, entry in enumerate(entries, start=1):
        entry["rank"] = i

    # 多治見を探す
    tajimi = next((e for e in entries if e["place"] == "多治見"), None)

    if not tajimi:
        raise Exception("多治見 not found!")

    return entries, tajimi, time

def save_json(entries, today_str, time):
    data = {
        "date": today_str,
        "data_time": time,
        "ranking": entries
    }

    os.makedirs("data", exist_ok=True)

    with open(f"data/{today_str}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_line_notify(message):
    token = os.environ.get("LINE_NOTIFY_TOKEN")
    if not token:
        print("LINE_NOTIFY_TOKEN not set")
        return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    res = requests.post(url, headers=headers, data=data)
    print(f"LINE Notify status: {res.status_code}")

if __name__ == "__main__":
    date_str, today_str = get_target_date()
    entries, tajimi, time = scrape_temperature(date_str)
    save_json(entries, today_str, time)

    # メッセージ
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    label = "[確定]" if now.hour < 3 else "[速報]"
    msg = f"{label} {today_str}\n多治見 {tajimi['temp']}℃ 全国{tajimi['rank']}位\n({tajimi['time']})\n({time})"

    send_line_notify(msg)
