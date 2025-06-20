import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import '../style/CreateGame.css';

const API_URL = 'http://localhost:8000/api';

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

const CreateGame: React.FC = () => {
  const [words, setWords] = useState<string[]>([]);
  const [currentWord, setCurrentWord] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [hostName, setHostName] = useState<string>("");

  const settings = useRef<Settings>(new Settings(60, 0, 3, 1));
  const navigate = useNavigate();

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

  const handleStartGame = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/game/create`, {
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

      if (!res.ok) throw new Error();
      const data = await res.json();
      navigate(`/lobby?code=${data.id}&name=${hostName}&host=true`);
    } catch {
      setError('Failed to create game. Please try again.');
    } finally {
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
  }

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

            <button type="button" className="action-button">
              Saved Desks
            </button>

            <button
              type="button"
              className="settings-button"
              onClick={() => setShowSettings(true)}
            >
              Settings
            </button>
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
