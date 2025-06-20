import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import '../style/Quiz.css';

import socketConfig from "./socketConfig";

// Gamestate returned from the server. It belongs to the player that requests it
interface GameState {
  current_word: string | null;
  expires_at: string | null;
  remaining_words_count: number;
  state: 'in_progress' | 'finished';
  tries_left: number;
  current_master: string;
  scores: { [name: string]: number };

}

const Quiz: React.FC = () => {
  // Information retrieved from URL (optimally to be replaced by global variables of some sort)
  const { gameId } = useParams<{ gameId: string }>();
  const urlParams = new URLSearchParams(window.location.search);
  const name = useRef<string>(urlParams.get("name"));
  const isHost = useRef<boolean>(urlParams.get("host") === "true");

  // Router functions
  const navigate = useNavigate();
  const location = useLocation();

  // Game states. Aside from WS, do not carry any function except from being displayed on the page
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [wrong, setWrong] = useState<string | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [timeStr, setTimeStr] = useState<string>("");
  const [attemptsLeft, setAttemptsLeft] = useState<number>();
  const [enteredWords, setEnteredWords] = useState<string[]>([]);
  const [inputWord, setInputWord] = useState<string>('');
  const [correctCount, setCorrectCount] = useState(0);
  const [ws, setWs] = useState<WebSocket | null>(null);


  // Variables to:
  const expiresAt = useRef<string>(""); // calculate time
  const triesLeft = useRef<number>(); // Keep track of wrong answers
  const score = useRef<number>(); // Keep track of right answers

  // Takes the "expires_at" field from the game state as an argument and adjusts for timezone to calculate time left for guessing
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

  // Connects to websocket (refers to socketConfig) and sets actions for different cases
  const connectWebSocket = useCallback(() => {
    if (!gameId || !name.current) { return; }

    // Host and player have different sockets:
    var websocket: WebSocket;
    isHost.current ? websocket = socketConfig.connectSocketHost(name.current, gameId) : websocket = socketConfig.connectSocketPlayer(name.current, gameId);

    websocket.onopen = () => {
      console.log('Connected to game server');
      setIsReconnecting(false);
      setError(null);
    };

    // When the game starts, the player gets the update first and then gets sent to this page, so the initial state transfered in
    // said update is carried out into location
    if (!isHost.current) {
      const initialState: GameState = location.state.game_state;
      setGameState(initialState);
      if (initialState.expires_at) {
        expiresAt.current = initialState.expires_at;
      }
      score.current = initialState.scores[name.current];
      triesLeft.current = initialState.tries_left;
      setAttemptsLeft(triesLeft.current);
      setCorrectCount(score.current);
    }

    // Stuff kinda self-explanatory
    websocket.onmessage = (event) => {
      const data: GameState = JSON.parse(event.data);
      setGameState(data);

      if (data.expires_at && data.expires_at !== expiresAt.current) {
        expiresAt.current = data.expires_at;
      }

      if (name.current && score.current === data.scores[name.current] && triesLeft.current !== data.tries_left) {
        setWrong("Wrong!");
      }

      else if (name.current && score.current !== data.scores[name.current]) {
        setWrong("Right!");
        score.current = data.scores[name.current];
        setEnteredWords([]);
        setCorrectCount(score.current);
      }

      triesLeft.current = data.tries_left;
      setAttemptsLeft(triesLeft.current);

      if (data.state === 'finished') {
        navigate(`/`); // <= to be changed to leaderboard
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

  // useEffect with (practically, since connectWebSocket is a function that does not change) an empty list to connect once
  useEffect(() => {
    connectWebSocket();
  }, [connectWebSocket]);

  // Sets a time interval to update the timer
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
    e.preventDefault(); // It is crucial, since most browsers do stupid stuff when submiting a form (e.g. reloading a page)
    console.log(inputWord);
    if (!inputWord.trim()) return;

    setEnteredWords([...enteredWords, inputWord]);
    const str = inputWord;
    ws?.send(JSON.stringify({ action: 'guess', guess: str }));
    setInputWord("");
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

  if (name.current === gameState.current_master) { // Quiz-card for the game master
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
  return ( // Playing field for the player
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
          <div className="score">Correct : {correctCount}</div>
        </div>

        <form onSubmit={handleSubmit} className="word-form">
          <input
            type="text"
            placeholder="Enter a word........"
            value={inputWord}
            onChange={(e) => setInputWord(e.target.value)}
            id="guess-input"
          />
          <button type="submit" disabled={ gameState.tries_left <= 0}>Submit</button>
        </form>
        <span>Attempts left {attemptsLeft}</span>
        <span>{ wrong }</span>
      </div>
    </div>
  )
};

export default Quiz; 