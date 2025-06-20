import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import '../style/Quiz.css';

import socketConfig from "./socketConfig";

/**
 * Interface defining the structure of the game state
 * @property current_word - The word currently being played
 * @property expires_at - Timestamp when the current word expires
 * @property remaining_words_count - Number of words left in the game
 * @property state - Current state of the game (in_progress or finished)
 */
interface GameState {
  current_word: string | null;
  expires_at: string | null;
  remaining_words_count: number;
  state: 'in_progress' | 'finished';
  tries_left: number;
  current_master: string;
  scores: { [name: string]: number };
}

// WebSocket server URL for real-time game updates
//const HOST = window.location.host;
const API_URL = "ws://" + "localhost:8000" + "/api";

/**
 * Quiz Component
 * 
 * This component handles the main gameplay experience:
 * 1. Establishes WebSocket connection for real-time game updates
 * 2. Displays current word and game progress
 * 3. Handles word skipping
 * 4. Manages game state and error handling
 * 5. Navigates to results page when game is finished
 */
const Quiz: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const urlParams = new URLSearchParams(window.location.search);
  const name = useRef<string>(urlParams.get("name"));
  const isHost = useRef<boolean>(urlParams.get("host") === "true");
  const [timeStr, setTimeStr] = useState<string>("");
  var expiresAt = useRef<string>("");

  const [enteredWords, setEnteredWords] = useState<string[]>([]);
  const inputWord = useRef<string>('');
  const [correctCount, setCorrectCount] = useState(0);
  const totalWords = 10; 

  /**
   * Formats the remaining time in a user-friendly way
   * @param expiresAt - The expiration timestamp
   * @returns string - Formatted time string
   */
  const formatTimeLeft = (expiresAt: string): string => {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diff = expires.getTime() - now.getTime() - expires.getTimezoneOffset() * 60000;

    if (diff <= 0) return 'Time\'s up!';

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  /**
   * Establishes WebSocket connection with reconnection logic
   */
  const connectWebSocket = useCallback(() => {
    if (!gameId || !name.current) { return; }

    var websocket: WebSocket;
    isHost.current ? websocket = socketConfig.connectSocketHost(name.current, gameId) : websocket = socketConfig.connectSocketPlayer(name.current, gameId);

    websocket.onopen = () => {
      console.log('Connected to game server');
      setIsReconnecting(false);
      setError(null);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setGameState(data);
      setEnteredWords([]);
      expiresAt.current = data.expires_at;

      if (data.state === 'finished') {
        navigate(`/`);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error. Please try again.');
    };

    websocket.onclose = (event) => {
      if (event.code === 1011) {
        setError('Game not found');
      } else if (event.code === 1008) {
        setError('Game already in progress');
      } else {
        setError('Connection closed. Attempting to reconnect...');
        setIsReconnecting(true);
      }
    };

    setWs(websocket);
  }, [gameId, navigate]);

  useEffect(() => {
    connectWebSocket();
  }, [connectWebSocket]);


  useEffect(() => {
    const interval = setInterval(() => {
      setTimeStr(formatTimeLeft(expiresAt.current));
    }, 500)

    return () => clearInterval(interval);
  }, [])


  const handleSkip = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'skip' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputWord.current.trim()) return;

    setEnteredWords([...enteredWords, inputWord.current]);
    const str = inputWord.current;
    ws?.send(JSON.stringify({ action: 'guess', str }));
    inputWord.current = '';
  };

  if (error) {
    return (
      <div className="quiz-container">
        <div className="error-message">{error}</div>
        {isReconnecting ? (
          <div className="reconnecting">Reconnecting...</div>
        ) : (
          <button onClick={() => navigate('/')} className="back-button">
            Back to Home
          </button>
        )}
      </div>
    );
  }

  if (!gameState) {
    return <div className="quiz-container">Loading...</div>;
  }

  if (name.current === gameState.current_master) {
    return (
      <div className="quiz-container">
        <div className="question-card">
          <div className="game-info">
            <div className="remaining-words">
              Words remaining: {gameState.remaining_words_count}
            </div>
            {gameState.expires_at && (
              <div className="timer">
                Time left: {timeStr}
              </div>
            )}
          </div>

          <h2>Current Word:</h2>
          <div className="current-word">
            {gameState.current_word || 'Waiting for next word...'}
          </div>

          <button onClick={handleSkip} className="skip-button">
            Skip Word
          </button>
        </div>

      </div>
    );
  }
  return (
    <div className="game-container">
      <div className="entered-words">
        <h4>Entered words:</h4>
        <ul>
          {enteredWords.map((word, i) => (
            <li key={i}>{word}</li>
          ))}
        </ul>
      </div>

      <div className="game-main">
        <div className="top-bar">
          <h2>Time left : {timeStr}</h2>
          <div className="score">Correct : {correctCount} / {totalWords}</div>
        </div>

        <form onSubmit={handleSubmit} className="word-form">
          <input
            type="text"
            placeholder="Enter a word........"
            value={inputWord.current}
            onChange={(e) => inputWord.current = e.target.value}
          />
          <button type="submit">Submit</button>
        </form>
      </div>
    </div>
  )
};

export default Quiz; 