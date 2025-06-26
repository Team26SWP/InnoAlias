export enum Page {
  Home = "Home",
  Join = "Join",
  Create = "Create",
  Quiz = "Quiz",
  Lobby = "Lobby",
  Leaderboard = "Leaderboard",
  Results = "Results",
  Login = "Login",
  Register = "Register",
  EmailConfirm = "EmailConfirm",
}

export interface Arguments {
  name : string;
  code : string;
  isHost : boolean;
}

export interface GameState {
  current_word: string | null;
  expires_at: string | null;
  remaining_words_count: number;
  state: 'in_progress' | 'finished';
  tries_left: number;
  current_master: string;
  scores: { [name: string]: number };
}

export interface Register{
  name: "",
  surname: "",
  email: "",
  password: "",
}

let hostSocket: WebSocket | null = null;
let playerSocket: WebSocket | null = null;

let initialState: GameState | null = null;

const HOST = "localhost:8000";
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
  console.log("Connection closed by the client");
  initialState = null;
}

let args : Arguments;

export function getArgs(){
  return args;
}

let regs : Register;

export function getRegs(){
  //return regs;
}

let _setCurrentPage: ((page: Page) => void) | null = null;

export function registerSetCurrentPage(fn: (page: Page) => void) {
  _setCurrentPage = fn;
}

export function navigateTo(page: Page, newArgs: Arguments = {name: "", code: "", isHost: false}) {
  if (!_setCurrentPage) {
    console.error("SetCurrentPage not registered!");
    return;
  }
  _setCurrentPage(page);
  args = newArgs;
}
export function setInitialState(init: GameState) {
  initialState = init;
}
export function getInitialState() {
  return initialState;
}