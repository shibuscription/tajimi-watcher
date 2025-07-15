export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).send("Method Not Allowed");
  }

  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  const rawBody = Buffer.concat(chunks).toString();
  const body = JSON.parse(rawBody);

  const event = body.events[0];
  const userText = event.message.text;
  const replyToken = event.replyToken;

  let replyMessage = "「今何位？」や「1位どこ？」って送ってくれたら教えるよ！";

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

  const isRankingRequest = /^(ランキング|top ?10|気温ランキング|10位まで)/i.test(userText);
  const nthRankMatch = userText.match(/^(\d{1,3})位どこ？?$/);

  if (userText.includes("何位") || userText.includes("1位") || isRankingRequest || nthRankMatch) {
    try {
      const csvRes = await fetch(csvUrl);
      const buffer = await csvRes.arrayBuffer();
      const iconv = (await import("iconv-lite")).default;
      const sjisText = iconv.decode(Buffer.from(buffer), "Shift_JIS");

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

      // 同率順位処理
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

      // ◯位どこ？（任意順位）
      if (nthRankMatch) {
        const requestedRank = parseInt(nthRankMatch[1], 10);
        const targetRows = valid.filter(row => row.rank === requestedRank);
        if (targetRows.length === 0) {
          replyMessage = `${requestedRank}位の地点は見つかりませんでした。`;
        } else {
          replyMessage = `【全国${requestedRank}位】\n\n`;
          replyMessage += targetRows.map(r =>
            `${r.都道府県} ${r.地点}：${r[tempCol]}℃（${r.起時}）`
          ).join("\n");
        }

      // ランキング（TOP10）
      } else if (isRankingRequest) {
        const top10 = valid.filter(row => row.rank <= 10);
        replyMessage = `【本日の気温ランキング TOP10】\n\n`;
        replyMessage += top10.map(r => {
          const emoji = r.rank === 1 ? '🥇' : r.rank === 2 ? '🥈' : r.rank === 3 ? '🥉' : '';
          return `${emoji}${r.rank}位 ${r.都道府県} ${r.地点} ${r[tempCol]}℃（${r.起時}）`;
        }).join("\n");

      // 今何位 or ◯◯は何位？
      } else if (userText.includes("何位")) {
        const sorted = valid.map(r => ({ ...r }));

        if (userText === "今何位？" || userText === "今何位" || userText.trim() === "今何位？") {
          const tajimi = sorted.find(r => r.地点 && r.地点.includes("多治見"));
          if (tajimi) {
            replyMessage = `🌡️ ${now.toISOString().slice(0, 10)}\n多治見は ${tajimi[tempCol]}℃ 全国${tajimi.rank}位！ (${tajimi.起時})`;
          } else {
            replyMessage = "多治見のデータが見つからなかった！";
          }
        } else {
          const keyword = userText.replace("は何位", "")
            .replace("何位", "")
            .replace("？", "")
            .replace("?", "")
            .trim();

          const matches = sorted.filter(r => r.地点 && r.地点.includes(keyword));

          if ((keyword === "" || keyword === "多治見") && matches.length === 0) {
            const tajimi = sorted.find(r => r.地点.includes("多治見"));
            if (tajimi) {
              replyMessage = `🌡️ ${now.toISOString().slice(0, 10)}\n多治見は ${tajimi[tempCol]}℃ 全国${tajimi.rank}位！ (${tajimi.起時})`;
            } else {
              replyMessage = `多治見のデータが見つからなかった！`;
            }
          } else if (matches.length === 0) {
            replyMessage = `${keyword}のデータが見つからなかったよ！`;
          } else if (matches.length === 1) {
            const r = matches[0];
            replyMessage = `🌡️ ${now.toISOString().slice(0, 10)}\n${r.都道府県} ${r.地点} は ${r[tempCol]}℃ 全国${r.rank}位！ (${r.起時})`;
          } else {
            const list = matches.slice(0, 5).map(r =>
              `${r.都道府県} ${r.地点}：${r[tempCol]}℃ 全国${r.rank}位（${r.起時}）`
            ).join("\n");
            replyMessage = `🏙️「${keyword}」を含む地点は複数あります：\n\n${list}`;
          }
        }

      // 1位どこ？
      } else if (userText.includes("1位")) {
        const top = valid[0];
        const topPref = top["都道府県"] || "";
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
