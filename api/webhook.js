export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).send("Method Not Allowed");
  }

  const body = req.body;
  console.log(JSON.stringify(body, null, 2));

  const event = body.events[0];
  const userText = event.message.text;
  const replyToken = event.replyToken;

  let replyMessage = "「今何位？」って送ってくれたら、多治見の順位を教えるよ！";

  if (userText.includes("何位")) {
    try {
      const latestRes = await fetch("https://shibuscription.github.io/tajimi-watcher/data/latest.json");
      const latest = await latestRes.json();
      const tajimi = latest.ranking.find((r) => r.地点.includes("多治見"));
      if (tajimi) {
        replyMessage = `🌡️ ${latest.date}\n多治見は ${tajimi.temp}℃ 全国${tajimi.rank}位！ (${tajimi.起時})`;
      } else {
        replyMessage = "多治見のデータが見つからなかったよ！";
      }
    } catch (e) {
      replyMessage = "ごめん、最新データを取れなかった！";
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
