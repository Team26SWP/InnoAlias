import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';


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
        navigate(`/leaderboard?code=${gameId}`, { state: {scores: data.scores} }); // <= to be changed to leaderboard
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
       <div className="flex flex-col items-center justify-center min-h-screen text-red-600 text-xl">
        <p>{error}</p>
        {isReconnecting ? <p>Reconnecting...</p> : <button className="mt-4 bg-blue-500 text-white px-4 py-2 rounded" onClick={() => navigate('/')}>Back to Home</button>}
      </div>
    );
  }

  

  if (!gameState) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
}

  if (name.current === gameState.current_master) { // Quiz-card for the game master
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#ffefe3] font-adlam text-[#3171a6]">
        <div className="text-xl mb-2">Words remaining: {gameState.remaining_words_count}</div>
        <div className="text-xl mb-6">Time left: {timeStr}</div>
        <div className="text-4xl font-bold bg-gray-200 px-12 py-8 rounded-xl shadow mb-4">
          {gameState.current_word || 'Waiting for next word...'}
        </div>
        <button onClick={handleSkip} className="mt-2 bg-[#3171a6] text-white px-6 py-3 rounded-lg hover:bg-[#2c5d8f]">Skip</button>
      </div>
    );
  }

  return ( // Playing field for the player
    <div className="flex flex-col md:flex-row min-h-screen bg-[#ffefe3] p-10 font-adlam">
      <div className="bg-[#d9d9d9] rounded-lg p-6 w-full md:w-1/2 min-h-[400px] mb-6 md:mb-0">
        <h2 className="text-2xl font-bold text-[#3171a6] border-b-4 border-[#3171a6] mb-4">Entered words:</h2>
        <ul className="text-[#3171a6]">
          {enteredWords.map((word, i) => <li key={i}>{word}</li>)}
        </ul>
      </div>
      <div className="flex-1 flex flex-col items-center">
        <div className="flex justify-between w-full max-w-xl mb-4 text-[#3171a6] font-bold">
          <h2>Time left: {timeStr}</h2>
          <div>Correct: {correctCount}</div>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col items-center w-full max-w-xl">
          <input
            type="text"
            placeholder="Enter a word........"
            value={inputWord}
            onChange={(e) => setInputWord(e.target.value)}
            className="w-full p-4 rounded-full bg-[#d9d9d9] text-[#3171a6] text-lg mb-4 focus:outline-none"
          />
          <button type="submit" disabled={gameState.tries_left <= 0} className="bg-[#3171a6] text-white px-8 py-2 rounded hover:bg-[#2c5d8f] disabled:opacity-50">Submit</button>
        </form>
        <span className="mt-2 text-[#3171a6]">Attempts left: {attemptsLeft}</span>
        <span className="mt-1 text-red-500 font-semibold">{wrong}</span>
      </div>
    </div>
  )
};

export default Quiz; 