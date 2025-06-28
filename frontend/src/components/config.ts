export enum Page {
  Home = 'Home',
  Join = 'Join',
  Create = 'Create',
  Quiz = 'Quiz',
  Lobby = 'Lobby',
  Leaderboard = 'Leaderboard',
  Results = 'Results',
  Login = 'Login',
  Register = 'Register',
  EmailConfirm = 'EmailConfirm',
  Profile = 'Profile',
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
export interface Deck {
  id: string;
  name: string;
  words_count: number;
  tags: string[];
}
export interface UserProfile {
  id: string;
  name: string;
  surname: string;
  email: string;
  decks: Deck[],
}
export class Settings {
  time: number;

  deckLimit: number;

  attemptsLimit: number;

  answersLimit: number;

  rotateMasters: boolean;

  constructor(
    time: number,
    deck: number,
    attempts: number,
    answers: number,
    rotateMasters: boolean,
  ) {
    this.time = time;
    this.deckLimit = deck;
    this.attemptsLimit = attempts;
    this.answersLimit = answers;
    this.rotateMasters = rotateMasters;
  }
}
export interface GameCreationState {
  settings: Settings;
  words: string[];
}

let hostSocket: WebSocket | null = null;
let playerSocket: WebSocket | null = null;

let initialState: GameState | null = null;
let rotation = false;
let deckChoice = false;

const creationState: GameCreationState = {
  settings: new Settings(60, 0, 3, 1, false),
  words: [],
};

const HOST = window.location.hostname;
export const WS_URL = `ws://${HOST}/api`;
export const HTTP_URL = `http://${HOST}/api`;

export function connectSocketHost(hostName: string, gameCode: string) {
  if (!hostSocket) {
    hostSocket = new WebSocket(`${WS_URL}/game/${gameCode}?name=${hostName}`);
  }
  return hostSocket;
}

export function connectSocketPlayer(playerName: string, gameCode: string) {
  if (!playerSocket) {
    playerSocket = new WebSocket(`${WS_URL}/game/player/${gameCode}?name=${playerName}`);
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
  initialState = null;
}

let args : Arguments;
let profile: UserProfile | null = null;

export function setProfile(newProfile: UserProfile | null) {
  profile = newProfile;
}

export function getProfile(): UserProfile | null {
  return profile;
}

export function getArgs() {
  return args;
}

let setCurrentPage: ((page: Page) => void) | null = null;

export function registerSetCurrentPage(fn: (page: Page) => void) {
  setCurrentPage = fn;
}

export function navigateTo(page: Page, newArgs: Arguments = { name: '', code: '', isHost: false }) {
  if (!setCurrentPage) {
    return;
  }
  setCurrentPage(page);
  args = newArgs;
}
export function setInitialState(init: GameState) {
  initialState = init;
}
export function getInitialState() {
  return initialState;
}
export function setRotation(newRotation: boolean) {
  rotation = newRotation;
}
export function getRotation() {
  return rotation;
}
export function setDeckChoice(newChoice: boolean) {
  deckChoice = newChoice;
}
export function getDeckChoice() {
  return deckChoice;
}
export function saveCreationState(settings: Settings, words: string[]) {
  creationState.settings = settings;
  creationState.words = words;
}
export function loadCreationState() {
  return creationState;
}
