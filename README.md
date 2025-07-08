
# 🌡️ たじみHOT BOT

全国有数の暑さを誇る岐阜県多治見市の  
**「今日の最高気温 & 全国順位」** をリアルタイムでチェックして通知する BOT です。

- 毎日 18:00 （速報）
- 毎日 1:00 （確定版）
- 気象庁公式の CSV データを直接取得して信頼性バッチリ
- LINE でプッシュ通知（Messaging API）
- Webhook で「今何位？」「1位どこ？」にリアルタイム返答
- JSON 保存や Pages は廃止してシンプル化

---

## 📌 何をしているの？

✅ 気象庁の「最新の気象データ」CSV を自動取得  
✅ `pandas` で全国データを読み込み、最高気温順に並べる  
✅ 多治見の気温と順位を抽出  
✅ LINE Messaging API で自分や友だちに通知  
✅ Vercel の Webhook で即時応答

---

## 🕐 更新スケジュール

| JST 時刻 | 内容   |
|-----------|--------|
| 17:00     | 当日の速報値 |
| 1:00 翌日 | 前日の確定値 |
| 任意      | LINE で「今何位？」と送ると即返事 |

---

## ⚡ 自動化の仕組み

- `GitHub Actions` で 1日2回 `scraper.py` を実行
- LINE にブロードキャスト通知
- Vercel にホスティングした `api/webhook.js` が返信

---

## 🗂️ 使っている技術

- Python 3.x
- pandas
- requests
- GitHub Actions
- Vercel（Node.js）
- LINE Messaging API

---

## 🪪 環境変数

| 名前 | 内容 |
|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot のチャネルアクセストークン |

---

## 📡 GitHub Actions

```yaml
- `.github/workflows/tajimi-checker.yml`  
  - `cron` で毎日2回実行
  - JSON 保存・Push は廃止
  - LINE にブロードキャスト通知のみ
```

---

## 🔗 Webhook

- Vercel にデプロイした `/api/webhook.js` が LINE Messaging API に連携  
- 「今何位？」「1位どこ？」で最新データをその場で取得して返答

---

## 🚩 注意点

- `LINE_CHANNEL_ACCESS_TOKEN` は Secrets に保存して漏洩防止
- JSON ファイル保存はしない（すべてリアルタイム）

---

## 🏁 つくった人

[しぶやん](https://github.com/shibuscription)  
多治見の暑さを自分で見守る人。

---

🌡️ **今年も暑さに負けないぞ！たじみHOT BOT！**
