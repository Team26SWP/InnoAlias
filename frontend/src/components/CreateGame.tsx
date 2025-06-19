import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../style/CreateGame.css';

const API_URL = '/api';

const CreateGame: React.FC = () => {
  const [words, setWords] = useState<string[]>([]);
  const [currentWord, setCurrentWord] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = currentWord.trim();
    if (trimmed) {
      setWords([...words, trimmed.toLowerCase()]);
      setCurrentWord('');
      setError(null);
    }

    const handleStartGame = () => {
   navigate("/lobby");
};
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
    if (!words.length) {
      setError('Please add at least one word');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/create/game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ remaining_words: words }),
      });

      if (!res.ok) throw new Error();
      const data = await res.json();
      navigate(`/game/${data.id}`);
    } catch {
      setError('Failed to create game. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="create-game-container">
      <h1 className="create-game-title">Create a Game</h1>
      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="word-form">
        <div className="input-container">
          <div className="left-section">
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
        disabled={words.length === 0 || isLoading}
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
                  <input type="number" /> <span>min</span>
                </div>
                <div className="time-unit">  
                  <input type="number" /> <span>sec</span>
                 </div>
              </div>
            </div>
            <div className="setting-row">
              <label>Deck limit:</label>
              <div className="row-right">
                <input type="number" /> <span>cards</span>
              </div>
            </div>
            <div className="setting-row">
              <label>Limit of attempts:</label>
              <div className="row-right">
                <input type="number" /> <span>tries</span>
              </div>
            </div>
            <div className="setting-row">
              <label>Limit of correct answers:</label>
              <div className="row-right">
                <input type="number" /> <span>players</span>
              </div>
            </div>

            <button className="modal-save-button">Save</button>
          </div>
        </div>
      </div>      
      )}
    </div>
  );
};

export default CreateGame;
