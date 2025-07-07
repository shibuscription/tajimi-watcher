#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import datetime
import json
import os

def get_target_date():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # JST
    if now.hour < 3:
        target_date = now - datetime.timedelta(days=1)
    else:
        target_date = now
    return target_date.strftime("%m%d"), target_date.strftime("%Y-%m-%d")

def scrape_temperature(date_str):
    url = f"http://www.data.jma.go.jp/obd/stats/data/mdrr/tem_rct/alltable/mxtemsad{date_str}.html"
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

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

    entries.sort(key=lambda x: x["temp"], reverse=True)

    for i, entry in enumerate(entries, start=1):
        entry["rank"] = i

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

def send_line_message(message):
    access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if not access_token or not user_id:
        print("LINE Messaging API credentials not set.")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    res = requests.post(url, headers=headers, json=payload)
    print(f"LINE Messaging API status: {res.status_code}")
    print(res.text)

if __name__ == "__main__":
    date_str, today_str = get_target_date()
    entries, tajimi, time = scrape_temperature(date_str)
    save_json(entries, today_str, time)

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    label = "[確定]" if now.hour < 3 else "[速報]"
    msg = f"{label} {today_str}\n多治見 {tajimi['temp']}℃ 全国{tajimi['rank']}位\n({tajimi['time']})\n({time})"

    send_line_message(msg)
