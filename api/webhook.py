from http.server import BaseHTTPRequestHandler
import json
import os
import requests

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LATEST_JSON_URL = "https://shibuscription.github.io/tajimi-watcher/data/latest.json"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        event = json.loads(body)

        for e in event["events"]:
            if e["type"] == "message" and e["message"]["type"] == "text":
                user_text = e["message"]["text"]
                reply_token = e["replyToken"]

                if "何位" in user_text:
                    msg = self.get_latest_rank()
                else:
                    msg = "「今何位？」って聞いてね！"

                self.reply(reply_token, msg)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def get_latest_rank(self):
        try:
            res = requests.get(LATEST_JSON_URL)
            latest = res.json()
            tajimi = next((x for x in latest["ranking"] if "多治見" in x["地点"]), None)
            if tajimi:
                return f"多治見は {tajimi['temp']}℃ 全国{tajimi['rank']}位！ ({tajimi['起時']})"
            return "多治見のデータがないよ！"
        except:
            return "最新データ取れなかった…"

    def reply(self, reply_token, text):
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
        }
        payload = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text}]
        }
        requests.post(url, headers=headers, json=payload)
