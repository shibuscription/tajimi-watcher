#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import datetime
import json
import os
import requests
import argparse

def get_target_url():
    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
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
    print(f"Columns: {df.columns.tolist()}")
    return df

def process_temperature(df):
    place_col = "地点"
    minute_col = "現在時刻(分)"

    minute_idx = df.columns.get_loc(minute_col)
    temp_col = df.columns[minute_idx + 1]
    hour_col = df.columns[minute_idx + 3]
    minute2_col = df.columns[minute_idx + 4]

    print(f"Detected temp_col: {temp_col}")

    df[temp_col] = pd.to_numeric(df[temp_col], errors="coerce")
    df = df.dropna(subset=[temp_col])
    df = df.sort_values(temp_col, ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    tajimi = df[df[place_col].str.contains("多治見", na=False)]
    if tajimi.empty:
        raise Exception("多治見 not found!")

    df["起時"] = df[hour_col].astype(int).astype(str) + ":" + df[minute2_col].astype(int).astype(str).str.zfill(2)

    # 🔥 ← 完全に NaN を None に！
    df = df.replace({pd.NA: None, pd.NaT: None, float('nan'): None})

    # ← Series も dict 化して NaN → None
    tajimi_row = tajimi.iloc[0].to_dict()
    tajimi_row = {k: (None if pd.isna(v) else v) for k, v in tajimi_row.items()}
    tajimi_row["起時"] = f"{int(tajimi.iloc[0][hour_col])}:{int(tajimi.iloc[0][minute2_col]):02d}"

    return df, tajimi_row, temp_col

def save_json(df, today_str):
    output = {
        "date": today_str,
        "ranking": df.to_dict(orient="records")
    }

    os.makedirs("data", exist_ok=True)
    with open(f"data/{today_str}.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, allow_nan=False)

    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, allow_nan=False)

def send_line_broadcast(message):
    access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

    if not access_token:
        print("LINE Messaging API token not set.")
        return

    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-line", action="store_true", help="LINE通知を送らない")
    args = parser.parse_args()

    url, today_str = get_target_url()
    df = fetch_csv(url)
    df, tajimi, temp_col = process_temperature(df)
    save_json(df, today_str)

    if not args.no_line:
        now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
        label = "[確定]" if now.hour < 3 else "[速報]"
        msg = f"{label} {today_str}\n本日の多治見は {tajimi[temp_col]}℃ で 全国{tajimi['rank']}位でした。\n({tajimi['起時']})"
        send_line_broadcast(msg)
