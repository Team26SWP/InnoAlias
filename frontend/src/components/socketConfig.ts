var hostSocket: WebSocket | null = null;
var playerSocket: WebSocket | null = null;

const HOST = window.location.host;
var WS_URL = "ws://" + HOST + "/api"
var HTTP_URL = "http://" + HOST + "/api"

function connectSocketHost(hostName: string, gameCode: string) {
  if (!hostSocket) {
    hostSocket = new WebSocket(`${WS_URL}/game/${gameCode}?name=${hostName}`);
    console.log("Called socket host");
  }
  return hostSocket;
}
function connectSocketPlayer(playerName: string, gameCode: string) {
  if (!playerSocket) {
    playerSocket = new WebSocket(`${WS_URL}/game/player/${gameCode}?name=${playerName}`);
    console.log("Called socket player");
  }
  return playerSocket;
}

function closeConnection() {
  if (hostSocket?.OPEN) {
    hostSocket.close();
    hostSocket = null;
  }
  if (playerSocket?.OPEN) {
    playerSocket.close();
    playerSocket = null;
  }
}


  export default { connectSocketHost, connectSocketPlayer, HTTP_URL, closeConnection};