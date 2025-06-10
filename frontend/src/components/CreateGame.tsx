import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../style/CreateGame.css';

const CreateGame: React.FC = () => {
  const [words, setWords] = useState<string[]>([]);
  const [currentWord, setCurrentWord] = useState('');
  const [gameCode, setGameCode] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentWord.trim()) {
      setWords([...words, currentWord.trim()]);
      setCurrentWord('');
    }
  };

  const handleStartGame = () => {
    if (words.length > 0 && gameCode.trim()) {
      // Here you can add logic to save the words and game code
      navigate(`/game/${gameCode.trim()}`);
    }
  };

  return (
    <div className="create-game-container">
      <h1 className="create-game-title">Create Word Game</h1>
      
      <div className="game-code-section">
        <input
          type="text"
          value={gameCode}
          onChange={(e) => setGameCode(e.target.value)}
          placeholder="Enter game code"
          className="game-code-input"
        />
      </div>

      <form onSubmit={handleSubmit} className="word-form">
        <div className="input-container">
          <input
            type="text"
            value={currentWord}
            onChange={(e) => setCurrentWord(e.target.value)}
            placeholder="Enter a word"
            className="word-input"
          />
          <button 
            type="submit"
            className="add-word-button"
          >
            Add Word
          </button>
        </div>
      </form>

      <div className="words-section">
        <h2 className="words-title">Added Words:</h2>
        <ul className="words-list">
          {words.map((word, index) => (
            <li 
              key={index}
              className="word-tag"
            >
              {word}
            </li>
          ))}
        </ul>
      </div>

      <button
        onClick={handleStartGame}
        disabled={words.length === 0 || !gameCode.trim()}
        className="start-game-button"
      >
        Start Game
      </button>
    </div>
  );
};

export default CreateGame;
