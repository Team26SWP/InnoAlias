export enum Page {
  Home = 'Home',
  Join = 'Join',
  Create = 'Create',
  AiCreate = 'AiCreate',
  Quiz = 'Quiz',
  AiGame = 'AiGame',
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

export interface AiGameState {
  _id: string;
  deck: string[];
  game_state: 'pending' | 'in_progress' | 'finished';
  settings: {
    time_for_guessing: number,
    word_amount: number,
  };
  remaining_words: string[];
  current_word: string | null;
  clues: string[];
  score: number;
  expires_at: string | null;
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
  decks: Deck[];
  isAdmin: boolean;
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
  aiGame: boolean;
}

// WebSocket instances
let hostSocket: WebSocket | null = null;
let playerSocket: WebSocket | null = null;
let aiSocket: WebSocket | null = null;

// Initial states (recieved from websoket in onmessage and transferred to other page)
let initialHostGameState: HostGameState | null = null;
let initialPlayerGameState: PlayerGameState | null = null;
let initialAiGameState: AiGameState | null = null;

// Supplementary variables to help with page management
let rotation = false;
let deckChoice = false;
let args : Arguments;
let profile: UserProfile | null = null;

// Game creation state to remember when loading a deck
const creationState: GameCreationState = {
  settings: new Settings(60, 0, 3, 1, false, 1),
  words: [],
  aiGame: false,
};

const HOST = window.location.hostname;
// const HOST = 'localhost:8000';
export const WS_URL = `ws://${HOST}/api`;
export const HTTP_URL = `http://${HOST}/api`;

// WebSocket functions
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

export function connectSocketAi(gameCode: string) {
  if (!aiSocket) {
    aiSocket = new WebSocket(`${WS_URL}/aigame/${gameCode}`);
  }
  return aiSocket;
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
  if (aiSocket && aiSocket.readyState === WebSocket.OPEN) {
    aiSocket.close();
    aiSocket = null;
  }
  initialHostGameState = null;
  initialPlayerGameState = null;
}

// Page navigation
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

export function getArgs() {
  return args;
}

// Profile
export function setProfile(newProfile: UserProfile | null) {
  profile = newProfile;
}

export function getProfile(): UserProfile | null {
  return profile;
}

// Initial states
export function setInitialHostState(init: HostGameState) { // Host
  initialHostGameState = init;
}
export function getInitialHostState() {
  return initialHostGameState;
}

export function setInitialPlayerState(init: PlayerGameState) { // Player
  initialPlayerGameState = init;
}
export function getInitialPlayerState() {
  return initialPlayerGameState;
}

export function setInitialAiState(init: AiGameState) { // Ai
  initialAiGameState = init;
}
export function getInitialAiState() {
  return initialAiGameState;
}

// Supplementary variables
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

// Game creation
export function resetGameCreation() {
  creationState.settings = new Settings(60, 0, 3, 1, false, 1);
  creationState.words = [];
  creationState.aiGame = false;
}
export function saveCreationState(settings: Settings, words: string[], aiGame: boolean = false) {
  creationState.settings = settings;
  creationState.words = words;
  creationState.aiGame = aiGame;
}
export function loadCreationState() {
  return creationState;
}

// Used to add words from a chosen deck into game creation
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
