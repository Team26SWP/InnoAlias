/* components/Config.ts */
export enum Page {
  Home = "Home",
  Join = "Join",
  Create = "Create",
  Quiz = "Quiz",
  Lobby = "Lobby",
  Leaderboard = "Leaderboard",
  Results = "Results",
}

let hostSocket: WebSocket | null = null;
let playerSocket: WebSocket | null = null;

const HOST = window.location.host;
export const WS_URL = `ws://${HOST}/api`;
export const HTTP_URL = `http://${HOST}/api`;

export function connectSocketHost(hostName: string, gameCode: string) {
  if (!hostSocket) {
    hostSocket = new WebSocket(`${WS_URL}/game/${gameCode}?name=${hostName}`);
    console.log("Called socket host");
  }
  return hostSocket;
}

export function connectSocketPlayer(playerName: string, gameCode: string) {
  if (!playerSocket) {
    playerSocket = new WebSocket(`${WS_URL}/game/player/${gameCode}?name=${playerName}`);
    console.log("Called socket player");
  }
  return playerSocket;
}

export function closeConnection() {
  if (hostSocket && hostSocket.readyState === WebSocket.OPEN) {
    hostSocket.close();
    hostSocket = null;
  }
  if (playerSocket && playerSocket.readyState === WebSocket.OPEN) {
    playerSocket.close();
    playerSocket = null;
  }
}

let _setCurrentPage: ((page: Page) => void) | null = null;

export function registerSetCurrentPage(fn: (page: Page) => void) {
  _setCurrentPage = fn;
}

export function navigateTo(page: Page) {
  if (!_setCurrentPage) {
    console.error("SetCurrentPage not registered!");
    return;
  }
  _setCurrentPage(page);
}

