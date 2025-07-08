export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).send("Method Not Allowed");
  }

  // 生のボディを読む
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  const rawBody = Buffer.concat(chunks).toString();
  const body = JSON.parse(rawBody);

  console.log("BODY:", body);

  const event = body.events[0];
  const userText = event.message.text;
  const replyToken = event.replyToken;

  let replyMessage = "「今何位？」って送ってくれたら教えるよ！";

  if (userText.includes("何位")) {
    try {
      const latestRes = await fetch("https://shibuscription.github.io/tajimi-watcher/data/latest.json");
      const latest = await latestRes.json();

      // 🔥 カラム名を動的に決定！
      const sample = latest.ranking[0];
      const keys = Object.keys(sample);
      const minute_col = "現在時刻(分)";
      const minute_idx = keys.indexOf(minute_col);
      const temp_col = keys[minute_idx + 1]; // ← これが当日の温度カラム

      console.log(`Detected temp_col: ${temp_col}`);

      const tajimi = latest.ranking.find((r) => r.地点.includes("多治見"));
      if (tajimi) {
        replyMessage = `🌡️ ${latest.date}\n多治見は ${tajimi[temp_col]}℃ 全国${tajimi.rank}位！ (${tajimi.起時})`;
      } else {
        replyMessage = "多治見のデータが見つからなかった！";
      }
    } catch (e) {
      console.error(e);
      replyMessage = "データ取得エラー！";
    }
  } else if (userText.includes("1位")) {
  // 1位どこ？パターン
  try {
    const latestRes = await fetch("https://shibuscription.github.io/tajimi-watcher/data/latest.json");
    const latest = await latestRes.json();

    const sample = latest.ranking[0];
    const keys = Object.keys(sample);
    const minute_col = "現在時刻(分)";
    const minute_idx = keys.indexOf(minute_col);
    const temp_col = keys[minute_idx + 1];

    const top = latest.ranking[0]; // 一番上が1位
    replyMessage = `🥇 ${latest.date}\n全国1位は ${top.地点} で ${top[temp_col]}℃！ (${top.起時})`;
  } catch (e) {
    console.error(e);
    replyMessage = "データ取得エラー！";
  }
}

  await fetch("https://api.line.me/v2/bot/message/reply", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.LINE_CHANNEL_ACCESS_TOKEN}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      replyToken,
      messages: [
        {
          type: "text",
          text: replyMessage
        }
      ]
    })
  });

  res.status(200).send("OK");
}
