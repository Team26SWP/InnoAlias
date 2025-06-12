import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../style/CreateGame.css';

const API_URL = 'http://localhost:8000';

/**
 * CreateGame Component
 * 
 * This component allows users to create a new word game by:
 * 1. Adding multiple words to a list
 * 2. Submitting the words to create a new game
 * 3. Navigating to the game page once created
 */
const CreateGame: React.FC = () => {
  // State to store the list of words added by the user
  const [words, setWords] = useState<string[]>([]);
  // State to manage the current word being typed in the input field
  const [currentWord, setCurrentWord] = useState('');
  // State to handle and display error messages
  const [error, setError] = useState<string | null>(null);
  // State to handle loading state
  const [isLoading, setIsLoading] = useState(false);
  // Hook for programmatic navigation
  const navigate = useNavigate();

  /**
   * Validates a word before adding it to the list
   * @param word - The word to validate
   * @returns string | null - Error message if invalid, null if valid
   */
  const validateWord = (word: string): string | null => {
    if (word.length < 2) {
      return 'Word must be at least 2 characters long';
    }
    if (word.length > 50) {
      return 'Word must be less than 50 characters';
    }
    if (!/^[a-zA-Z\s-]+$/.test(word)) {
      return 'Word can only contain letters, spaces, and hyphens';
    }
    if (words.includes(word.toLowerCase())) {
      return 'This word has already been added';
    }
    return null;
  };

  /**
   * Handles the form submission when adding a new word
   * Adds the current word to the words list if it's not empty
   * @param e - Form event object
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedWord = currentWord.trim();
    
    if (trimmedWord) {
      const validationError = validateWord(trimmedWord);
      if (validationError) {
        setError(validationError);
        return;
      }
      setWords([...words, trimmedWord.toLowerCase()]);
      setCurrentWord('');
      setError(null);
    }
  };

  /**
   * Handles the game creation process
   * Sends the list of words to the backend to create a new game
   * Navigates to the game page on success
   * Displays error message if the process fails
   */
  const handleStartGame = async () => {
    if (words.length === 0) {
      setError('Please add at least one word');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/create/game`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          remaining_words: words
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create game');
      }

      const data = await response.json();
      navigate(`/lobby/${data.id}`);
    } catch (err) {
      setError('Failed to create game. Please try again.');
      console.error('Error creating game:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="create-game-container">
      <h1 className="create-game-title">Create Word Game</h1>
      
      {/* Display error message if any */}
      {error && <div className="error-message">{error}</div>}

      {/* Form for adding new words */}
      <form onSubmit={handleSubmit} className="word-form">
        <div className="input-container">
          <input
            type="text"
            value={currentWord}
            onChange={(e) => {
              setCurrentWord(e.target.value);
              setError(null);
            }}
            placeholder="Enter a word"
            className="word-input"
            disabled={isLoading}
          />
          <button 
            type="submit"
            className="add-word-button"
            disabled={isLoading}
          >
            Add Word
          </button>
        </div>
      </form>

      {/* Display section for added words */}
      <div className="words-section">
        <h2 className="words-title">Added Words ({words.length}):</h2>
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

      {/* Button to start the game - disabled if no words are added */}
      <button
        onClick={handleStartGame}
        disabled={words.length === 0 || isLoading}
        className="start-game-button"
      >
        {isLoading ? 'Creating Game...' : 'Start Game'}
      </button>
    </div>
  );
};

export default CreateGame;
