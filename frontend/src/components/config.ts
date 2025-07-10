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
  Host = 'Host',
}

export interface Arguments {
  name : string;
  code : string;
  isHost : boolean;
}

export interface PlayerGameState {
  game_state: 'in_progress' | 'finished' | 'pending';
  expires_at: string | null;
  current_word: string | null;
  current_master: string;
  remaining_words_count: number;
  tries_left: number;
  team_id: string;
  team_name: string;
  team_scores: { [id: string]: number };
  players_in_team: string[];
  all_teams_scores: { [id: string]: number };
  winning_team: string;
}

export interface TeamGameState {
  id: string;
  name: string;
  remaining_words_count: number;
  current_word: string;
  expires_at: string;
  current_master: string;
  state: 'pending' | 'in_progress' | 'finished';
  scores: { [id: string]: number };
  players: string[];
  current_correct: number;
  right_answers_to_advance: number;
}

export interface HostGameState {
  game_state: 'pending' | 'in_progress' | 'finished';
  teams: { [team_id: string]: TeamGameState };
  winning_team: string;
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

  numberOfTeams: number;

  constructor(
    time: number,
    deck: number,
    attempts: number,
    answers: number,
    rotateMasters: boolean,
    numberOfTeams: number,
  ) {
    this.time = time;
    this.deckLimit = deck;
    this.attemptsLimit = attempts;
    this.answersLimit = answers;
    this.rotateMasters = rotateMasters;
    this.numberOfTeams = numberOfTeams;
  }
}
export interface GameCreationState {
  settings: Settings;
  words: string[];
}

let hostSocket: WebSocket | null = null;
let playerSocket: WebSocket | null = null;

let initialHostGameState: HostGameState | null = null;
let initialPlayerGameState: PlayerGameState | null = null;
let rotation = false;
let deckChoice = false;

const creationState: GameCreationState = {
  settings: new Settings(60, 0, 3, 1, false, 1),
  words: [],
};

const HOST = 'localhost:8000';
export const WS_URL = `ws://${HOST}/api`;
export const HTTP_URL = `http://${HOST}/api`;

export function connectSocketHost(hostId: string, gameCode: string) {
  if (!hostSocket) {
    hostSocket = new WebSocket(`${WS_URL}/game/${gameCode}?id=${hostId}`);
  }
  return hostSocket;
}

export function connectSocketPlayer(playerName: string, gameCode: string) {
  if (!playerSocket) {
    playerSocket = new WebSocket(`${WS_URL}/game/player/${gameCode}?name=${playerName}&team_id=team_1`);
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
  initialHostGameState = null;
  initialPlayerGameState = null;
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
export function setInitialHostState(init: HostGameState) {
  initialHostGameState = init;
}
export function setInitialPlayerState(init: PlayerGameState) {
  initialPlayerGameState = init;
}
export function getInitialPlayerState() {
  return initialPlayerGameState;
}
export function getInitialHostState() {
  return initialHostGameState;
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
export function resetGameCreation() {
  creationState.settings = new Settings(60, 0, 3, 1, false, 1);
  creationState.words = [];
}
export function saveCreationState(settings: Settings, words: string[]) {
  creationState.settings = settings;
  creationState.words = words;
}
export function loadCreationState() {
  return creationState;
}
export function addWords(words: string[]) {
  for (let i = 0; i < words.length; i += 1) {
    let addition = true;
    for (let j = 0; j < creationState.words.length; j += 1) {
      if (creationState.words[j].toLowerCase() === words[i].toLowerCase()) {
        addition = false;
        break;
      }
    }
    if (addition) {
      creationState.words.push(words[i]);
    }
  }
}
