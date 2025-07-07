
# 🌡️ 多治見ウォッチャー

全国有数の暑さを誇る岐阜県多治見市の  
**「今日の最高気温 & 全国順位」** を自動でチェックする BOT です。

- 毎日 18:00 （速報）
- 毎日 1:00 （確定版）
- 気象庁公式の CSV データを使って信頼性バッチリ
- 全国ランキング JSON を自動生成
- LINE でプッシュ通知
- JSON は GitHub Pages で即公開

---

## 📌 何をしているの？

✅ 気象庁の「最新の気象データ」CSV を自動取得  
✅ `pandas` で全国データを読み込み、最高気温順に並べる  
✅ 多治見の気温と順位を抽出  
✅ LINE Messaging API で自分に通知  
✅ JSON に保存して GitHub Pages で配信

---

## ⚙️ データの場所

- **最新データ**  
  [`/data/latest.json`](./data/latest.json)

- **日付別バックアップ**  
  `/data/YYYY-MM-DD.json`

---

## 🕐 更新スケジュール

| JST 時刻 | 内容   |
|-----------|--------|
| 18:00     | 当日の速報値 |
| 1:00 翌日 | 前日の確定値 |

---

## ⚡ 自動化の仕組み

- `GitHub Actions` で 1日2回 `scraper.py` を実行
- JSON をコミット & Push
- Pages で即ホスト
- LINE は Messaging API で直接プッシュ

---

## 🗂️ 使っている技術

- Python 3.x
- pandas
- requests
- GitHub Actions
- GitHub Pages
- LINE Messaging API

---

## 🪪 環境変数

| 名前 | 内容 |
|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot のチャネルアクセストークン |
| `LINE_USER_ID` | 通知を送る LINE ユーザーID |
| `GITHUB_TOKEN` | Actions で自動注入（手動設定不要） |

---

## 📡 GitHub Actions

```yaml
- `.github/workflows/tajimi-checker.yml`  
  - `cron` で毎日2回実行
  - JSON を `data/` に保存して自動コミット & Push
```

---

## 🚩 注意点

- JSON は GitHub Pages で誰でも取得可能
- `LINE_USER_ID` は Secrets に保存して漏洩防止
- `github-pages` Environment は `Deploy from a branch` モードなので自動で動作

---

## 🏁 つくった人

[しぶやん](https://github.com/shibuscription)  
多治見の暑さを自分で見守る人。

---

🌡️ **今年も暑さに負けないぞ！**
