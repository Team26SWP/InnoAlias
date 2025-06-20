var hostSocket: WebSocket | null = null;
var playerSocket: WebSocket | null = null;

var WS_URL = "ws://localhost:8000/api"

function connectSocketHost(hostName: string, gameCode: string) {
  if (!hostSocket) {
    hostSocket = new WebSocket(`${WS_URL}/game/${gameCode}?name=${hostName}`);
    console.log("Called socket host");
  }
  return hostSocket;
}
function connectSocketPlayer(playerName: string, gameCode: string) {
  if (!playerSocket) {
    playerSocket = new WebSocket(`${WS_URL}/game/player/${gameCode}/?name=${playerName}`);
    console.log("Called socket player");
  }
  return playerSocket;
}

export default { connectSocketHost, connectSocketPlayer };