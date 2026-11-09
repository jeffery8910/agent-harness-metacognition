// S1 判定權在伺服器：同一組搶答，用客戶端時間判 vs 用伺服器時間判。
// 執行：node judge.mjs
//
// 情境：三個玩家按下搶答。小美的手機時鐘快了 2 秒（或被竄改），
// 她回報的時間看起來最早，但伺服器其實最晚才收到她的訊息。

const buzzes = [
  // receivedAt：伺服器收到的時間（毫秒，伺服器自己的時鐘）
  // clientTime：手機自己回報的時間
  { player: "阿明", receivedAt: 1000, clientTime: 980 },
  { player: "小華", receivedAt: 1040, clientTime: 1010 },
  { player: "小美", receivedAt: 1120, clientTime: 900 },
];

function judgeByClient(list) {
  return [...list].sort((a, b) => a.clientTime - b.clientTime)[0].player;
}

// 伺服器端判定：只看自己觀察到的順序。
// 在 Cloudflare Durable Object 裡，同一個房間的訊息會依序處理，
// 第一個抵達的就是第一名，不需要也不應該採信 clientTime。
function judgeByServer(list) {
  return [...list].sort((a, b) => a.receivedAt - b.receivedAt)[0].player;
}

const byClient = judgeByClient(buzzes);
const byServer = judgeByServer(buzzes);

console.log(`用客戶端時間判定：${byClient} 先按`);
console.log(`用伺服器時間判定：${byServer} 先按`);
console.log(
  byClient === byServer
    ? "兩種判定結果一致"
    : "兩種判定結果不同：關鍵判定要以伺服器觀察到的資料為準"
);

export { buzzes, judgeByClient, judgeByServer };
