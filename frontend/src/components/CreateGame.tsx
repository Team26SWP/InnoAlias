import React, { useState, useRef, useEffect } from 'react';
import '../style/CreateGame.css';

import * as Config from './Config';

class Settings {
  time: number;
  deckLimit: number;
  attemptsLimit: number;
  answersLimit: number;
  constructor(time: number, deck: number, attempts: number, answers: number) {
    this.time = time;
    this.deckLimit = deck;
    this.attemptsLimit = attempts;
    this.answersLimit = answers;
  }
}

interface Deck {
  name: string;
  cards: string[];
}

const CreateGame: React.FC = () => {
  const [words, setWords] = useState<string[]>([]);
  const [currentWord, setCurrentWord] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [hostName, setHostName] = useState<string>("");
  const [decks, setDecks] = useState<Deck[]>([]);
  const settings = useRef<Settings>(new Settings(60, 0, 3, 1));
  const socketRef = useRef<WebSocket | null>(null);
  

  useEffect(() => {
    const cookies = document.cookie.replaceAll("[", "").replaceAll("]", "");
    if (!cookies) return;
    var deckStrings: string[] = cookies.split(";");
    var supplementaryArray: Deck[] = [];
    for (let i = 0; i < deckStrings.length; i++) {
      const parsedString = deckStrings[i].split("=");
      supplementaryArray.push({ name: parsedString[0], cards: parsedString[1].split(",") });
    }
    setDecks(supplementaryArray);
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = currentWord.trim();
    if (trimmed) {
      setWords([...words, trimmed.toLowerCase()]);
      setCurrentWord('');
      setError(null);
    }
  };

  const parse = (text: string) => {
    const lines = text
      .split(/\r?\n/)
      .map(l => l.trim())
      .filter(l => l.length);
    setWords(ws => [...ws, ...lines]);
  };

  const fileSubmit = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) file.text().then(parse);
  };

  const loadDeck = () => {
    const selector = document.getElementById("selector");
    if (!(selector instanceof HTMLSelectElement)) return;
    const cards = selector.value;
    if (!cards) return;
    setWords(words.concat(cards.split(",")));
  }

  const handleStartGame = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${Config.HTTP_URL}/game/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          remaining_words: words,
          words_amount: (settings.current.deckLimit === 0) ? words.length : settings.current.deckLimit,
          time_for_guessing: settings.current.time,
          tries_per_player: settings.current.attemptsLimit,
          right_answers_to_advance: settings.current.answersLimit
        }),
      });

      if (!response.ok) throw new Error();
      const data = await response.json();
      const gameCode = data.id;

      const socket = Config.connectSocketHost(hostName, gameCode);
      socketRef.current = socket;

      socket.onopen = () => {
        Config.navigateTo(Config.Page.Lobby, { name: hostName, code: gameCode, isHost: true });
      };

      socket.onerror = () => {
        setError('Failed to connect host socket.');
        setIsLoading(false);
      };
    } catch {
      setError('Failed to create game. Please try again.');
      setIsLoading(false);
    }
  };

  const saveSettings = () => {
    const minutes = document.getElementById("minutes");
    const seconds = document.getElementById("seconds");
    const deckLimit = document.getElementById("deck-length");
    const attemptLimit = document.getElementById("attempts");
    const answerLimit = document.getElementById("answers");
    if (minutes instanceof HTMLInputElement && seconds instanceof HTMLInputElement && deckLimit instanceof HTMLInputElement && attemptLimit instanceof HTMLInputElement && answerLimit instanceof HTMLInputElement) {
      settings.current.time = parseInt((minutes.value !== "") ? minutes.value : "1") * 60 + parseInt((seconds.value !== "") ? seconds.value : "0");
      if (settings.current.time === 0) settings.current.time = 1;
      settings.current.deckLimit = parseInt((deckLimit.value !== "") ? deckLimit.value : "0");
      settings.current.attemptsLimit = parseInt((attemptLimit.value !== "") ? attemptLimit.value : "3");
      settings.current.answersLimit = parseInt((answerLimit.value !== "") ? answerLimit.value : "1");
    }
    setShowSettings(false);
  }

  useEffect(() => {
    return () => {
      socketRef.current?.close();
      Config.closeConnection();
    };
  }, []);

  return (
    <div className="create-game-container">
      <h1 className="create-game-title">Create a Game</h1>
      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="word-form">
        <div className="input-container">
          <div className="left-section">
            <input type="text" className="word-input" placeholder="Enter your name"
            value={hostName}
            onChange={(e) => { setHostName(e.target.value); setError(null) } } />
            <input
              type="text"
              className="word-input"
              placeholder="Enter a word"
              value={currentWord}
              onChange={(e) => {
                setCurrentWord(e.target.value);
                setError(null);
              }}
            />
            <div className="words-section">
              <h2 className="words-title">Added Words ({words.length}):</h2>
              <ul className="words-list">
                {words.map((w, i) => (
                  <li key={i} className="word-tag">
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="actions-container">
            <button type="submit" className="add-word-button">Add Word</button>

            <label className="custom-file-upload">
              <input type="file" accept=".txt" onChange={fileSubmit} />
              Import via txt
            </label>

            <button
              type="button"
              className="settings-button"
              onClick={() => setShowSettings(true)}
            >
              Settings
            </button>

            <button type="button" className="action-button" onClick={loadDeck}>
              Load a saved deck
            </button>

            <select className="deckSelect" id="selector">
              <option value="">Select a deck</option>
              {decks.map((deck, i) => (<option key={i} value={deck.cards}>{deck.name}</option> ))}
            </select>
          </div>
        </div>
      </form>

      <button
        onClick={handleStartGame}
        disabled={words.length === 0 || isLoading || hostName === ""}
        className="start-game-button"
      >
        {isLoading ? 'Creating Game...' : 'Start Game'}
      </button>

      {showSettings && (
        <div className="modal-overlay">
          <div className="modal">
            <button className="modal-close" onClick={() => setShowSettings(false)}>
              ✕
            </button>
            <div className="modal-content">
              <div className="setting-row">
                <label>Time:</label>
                <div className="row-right time-group">
                  <div className="time-unit">
                    <input type="number" id="minutes" min="0" max="59" placeholder="1"/> <span>min</span>
                  </div>
                  <div className="time-unit">
                    <input type="number" id="seconds" min="0" max="59" placeholder="0"/> <span>sec</span>
                  </div>
                </div>
              </div>
              <div className="setting-row">
                <label>Deck limit:</label>
                <div className="row-right">
                  <input type="number" id="deck-length" placeholder="max" min="1"/> <span>cards</span>
                </div>
              </div>
              <div className="setting-row">
                <label>Limit of attempts:</label>
                <div className="row-right">
                  <input type="number" id="attempts" placeholder="3" min="1"/> <span>tries</span>
                </div>
              </div>
              <div className="setting-row">
                <label>Limit of correct answers:</label>
                <div className="row-right">
                  <input type="number" id="answers" placeholder="1" min="1"/> <span>players</span>
                </div>
              </div>

              <button className="modal-save-button" onClick={saveSettings}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CreateGame;
