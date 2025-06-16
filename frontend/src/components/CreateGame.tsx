import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../style/CreateGame.css';

const API_URL = 'http://localhost:8000/api';

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
  const [fileWords, setFileWords] = useState<string[]>([]);
  // State to manage the current word being typed in the input field
  const [currentWord, setCurrentWord] = useState('');
  // State to handle and display error messages
  const [error, setError] = useState<string | null>(null);
  // State to handle loading state
  const [isLoading, setIsLoading] = useState(false);
  // Hook for programmatic navigation
  const navigate = useNavigate();
    let fileImportField = useRef<HTMLElement | null>(null);
    let wordInputField = useRef<HTMLTextAreaElement | null>(null);
  /**
   * Handles the form submission when adding a new word
   * Adds the current word to the words list if it's not empty
   * @param e - Form event object
   */

    const getWords = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        if (event.target.textContent != null) {
            setWords(event.target.value.split(/\r?\n/).map(line => line.trim()).filter(line => line.length > 0));
        }
    }

    function handleImportClick() {
        if (fileImportField.current != null) {
            fileImportField.current.click();
        } else console.log("lol")
    }

    function parse(wordsString: string) {
        const addingWords = wordsString.split(/\r?\n/).map(line => line.trim()).filter(line => line.length > 0);
        setWords(addingWords.concat(words));
        if (wordInputField.current != null) {
            wordInputField.current.value = addingWords.concat(words).join("\n");
            wordInputField.current.scrollTop = wordInputField.current.scrollHeight;
        }
    }

    const fileSubmit = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files != null) {
            if (event.target.files[0] != undefined) {
                event.target.files[0].text().then(parse);
            }
        }
    }

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
      navigate(`/game/${data.id}`);
    } catch (err) {
      setError('Failed to create game. Please try again.');
      console.error('Error creating game:', err);
    } finally {
      setIsLoading(false);
    }
    };  

    useEffect(() => {
        fileImportField.current = document.getElementById("add-words-import");
        wordInputField.current = document.getElementById("words-input-field") as HTMLTextAreaElement;
    }, [])

  return (
    <div className="create-game-container">
      <h1 className="create-game-title">Create Word Game</h1>
      
      {/* Display error message if any */}
      {error && <div className="error-message">{error}</div>}

      {/* Form for adding new words */}
        <div className="input-container">
          <textarea 
            onChange={getWords}
            placeholder="Enter your words"
            className="word-input"
            disabled={isLoading}
            id="words-input-field"
          />

          
        </div>
      
          <button onClick={handleImportClick} className="file-import-btn">
          <input type="file" accept=".txt" id="add-words-import" onChange={fileSubmit} />
              Upload a file
        </button>
        {/* Button to start the game - disabled if no words are added */}
      <button
          onClick={handleStartGame}
          disabled={words.length === 0 && fileWords.length === 0 || isLoading}
          className="start-game-button">
          {isLoading ? 'Creating Game...' : 'Start Game'}
      </button>
      
    </div>
  );
};

export default CreateGame;
