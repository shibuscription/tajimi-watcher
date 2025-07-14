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

  let replyMessage = "「今何位？」か「1位どこ？」って送ってくれたら教えるよ！";

  // ---- ▼ Pythonのget_target_url()相当 ▼ ----
  const now = new Date(new Date().getTime() + 9 * 60 * 60 * 1000); // JST
  let csvUrl;
  if (now.getHours() < 3) {
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const mm = String(yesterday.getMonth() + 1).padStart(2, '0');
    const dd = String(yesterday.getDate()).padStart(2, '0');
    csvUrl = `https://www.data.jma.go.jp/stats/data/mdrr/tem_rct/alltable/mxtemsadext${mm}${dd}.csv`;
  } else {
    csvUrl = `https://www.data.jma.go.jp/stats/data/mdrr/tem_rct/alltable/mxtemsadext00_rct.csv`;
  }

  if (userText.includes("何位") || userText.includes("1位")) {
    try {
      // CSV を Shift_JIS で取る
      const csvRes = await fetch(csvUrl);
      const buffer = await csvRes.arrayBuffer();
      const iconv = (await import("iconv-lite")).default;
      const sjisText = iconv.decode(Buffer.from(buffer), "Shift_JIS");

      // CSV をパース
      const Papa = (await import("papaparse")).default;
      const parsed = Papa.parse(sjisText, { header: true });

      const df = parsed.data.filter((row) => row.地点);
      const keys = Object.keys(df[0]);
      const minuteCol = "現在時刻(分)";
      const minuteIdx = keys.indexOf(minuteCol);
      const tempCol = keys[minuteIdx + 1];
      const hourCol = keys[minuteIdx + 3];
      const minute2Col = keys[minuteIdx + 4];

      df.forEach(row => {
        row[tempCol] = parseFloat(row[tempCol]);
      });

      const valid = df.filter(row => !isNaN(row[tempCol]))
        .sort((a, b) => b[tempCol] - a[tempCol]);

      // ✅ 同率順位対応
      let prevTemp = null;
      let rank = 0;
      valid.forEach((row, idx) => {
        if (row[tempCol] !== prevTemp) {
          rank = idx + 1;
          prevTemp = row[tempCol];
        }
        row.rank = rank;
        row.起時 = `${parseInt(row[hourCol])}:${String(parseInt(row[minute2Col])).padStart(2, '0')}`;
      });

      if (userText.includes("何位")) {
        const tajimi = valid.find(r => r.地点.includes("多治見"));
        if (tajimi) {
          replyMessage = `🌡️ ${now.toISOString().slice(0, 10)}\n多治見は ${tajimi[tempCol]}℃ 全国${tajimi.rank}位！ (${tajimi.起時})`;
        } else {
          replyMessage = "多治見のデータが見つからなかった！";
        }
      } else if (userText.includes("1位")) {
        const top = valid[0];
        const topPref = top["都道府県"] || "";
        replyMessage = `🥇 ${now.toISOString().slice(0, 10)}\n全国1位は ${top.地点} ${top[tempCol]}℃ (${top.起時})`;
        replyMessage = `🥇 ${now.toISOString().slice(0, 10)}\n全国1位は ${top.地点}（${topPref}） ${top[tempCol]}℃ (${top.起時})`;
      }
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
