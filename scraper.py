#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import datetime
import json
import os
import requests

def get_target_url():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # JST
    if now.hour < 3:
        target_date = now - datetime.timedelta(days=1)
        date_str = target_date.strftime("%m%d")
        url = f"https://www.data.jma.go.jp/stats/data/mdrr/tem_rct/alltable/mxtemsadext{date_str}.csv"
    else:
        url = "https://www.data.jma.go.jp/stats/data/mdrr/tem_rct/alltable/mxtemsadext00_rct.csv"

    today_str = target_date.strftime("%Y-%m-%d") if now.hour < 3 else now.strftime("%Y-%m-%d")
    return url, today_str

def fetch_csv(url):
    print(f"Fetching CSV: {url}")
    df = pd.read_csv(url, encoding="shift_jis")
    return df

def process_temperature(df):
    # 1列目: 順位が無い場合があるので、独自に並び替え
    df["気温"] = pd.to_numeric(df["気温"], errors="coerce")
    df = df.dropna(subset=["気温"])
    df = df.sort_values("気温", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    # 多治見
    tajimi = df[df["地点"].str.contains("多治見", na=False)]
    if tajimi.empty:
        raise Exception("多治見 not found!")

    tajimi_row = tajimi.iloc[0]
    return df, tajimi_row

def save_json(df, today_str):
    output = {
        "date": today_str,
        "ranking": df.to_dict(orient="records")
    }

    os.makedirs("data", exist_ok=True)
    with open(f"data/{today_str}.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

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
    url, today_str = get_target_url()
    df = fetch_csv(url)
    df, tajimi = process_temperature(df)
    save_json(df, today_str)

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    label = "[確定]" if now.hour < 3 else "[速報]"
    msg = f"{label} {today_str}\n多治見 {tajimi['気温']}℃ 全国{tajimi['rank']}位\n({tajimi['時刻']})"
    send_line_message(msg)
