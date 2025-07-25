import React, {
  useState, useEffect, useCallback, useRef,
} from 'react';
import * as config from './config';

interface StackCardProps {
  word: string
  layerCount?: number
  offsetPx?: number
}

function StackCard({
  word,
  layerCount = 4,
  offsetPx = 6,
}: StackCardProps) {
  const layers = Array.from({ length: layerCount }, (_, i) => i);

  return (
    <div className="relative w-80 h-48 mb-6">
      {layers.map((i) => (
        <div
          key={i}
          className="absolute left-0 right-0 rounded-2xl flex items-center justify-center"
          style={{
            top: `${i * offsetPx}px`,
            height: '100%',
            backgroundColor:
              i === 0
                ? '#DBD9D1'
                : `rgba(217, 217, 217, ${0.8 - i * (0.8 / layerCount)})`,
            zIndex: layerCount - i,
          }}
        >
          {i === 0 && (
            <span className="text-4xl font-bold text-primary">
              {word}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

StackCard.defaultProps = {
  layerCount: 4,
  offsetPx: 6,
};

function Quiz() {
  const args = useRef<config.Arguments>({ name: '', code: '', isHost: false });

  // Game states. Aside from WS, do not carry any function except from being displayed on the page
  const [gameState, setGameState] = useState<null | config.PlayerGameState>(null);
  const [error, setError] = useState<string | null>(null);
  const [wrong, setWrong] = useState<string | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [timeStr, setTimeStr] = useState<string>('');
  const [attemptsLeft, setAttemptsLeft] = useState<number>();
  const [enteredWords, setEnteredWords] = useState<string[]>([]);
  const [inputWord, setInputWord] = useState<string>('');
  const [correctCount, setCorrectCount] = useState(0);
  const [totalWords, setTotalWords] = useState<number>(0);
  const ws = useRef<WebSocket | null>(null);

  // Variables to:
  const expiresAt = useRef<string>(''); // calculate time
  const triesLeft = useRef<number>(); // Keep track of wrong answers
  const score = useRef<number>(); // Keep track of right answers

  // Takes the "expires_at" field from the game state as an argument and adjusts for timezone
  // to calculate time left for guessing
  const formatTimeLeft = (endTime: string): string => {
    const now = new Date();
    const expires = new Date(endTime);
    const diff = expires.getTime() - now.getTime() - expires.getTimezoneOffset() * 60000;

    if (diff <= 0) return 'Time\'s up!';

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Connects to websocket (refers to config) and sets actions for different cases
  const connectWebSocket = useCallback(() => {
    const { name, code } = args.current;
    if (!code || !name) return;

    // Host and player have different sockets:
    const websocket = config.connectSocketPlayer(name, code);

    // Stuff kinda self-explanatory
    websocket.onmessage = (event) => {
      const data: config.PlayerGameState = JSON.parse(event.data);
      setGameState(data);

      if (data.expires_at && data.expires_at !== expiresAt.current) {
        expiresAt.current = data.expires_at;
      }

      if (name && score.current !== data.team_scores[name]) { // Correct guess
        setWrong('Right!');
        score.current = data.team_scores[name];
        setEnteredWords([]);
        setCorrectCount(score.current);
      } else if (name && score.current === data.team_scores[name]
        && triesLeft.current !== data.tries_left) { // Wrong guess
        setWrong('Wrong!');
      }

      triesLeft.current = data.tries_left;
      setAttemptsLeft(triesLeft.current);

      if (data.game_state === 'finished') {
        config.navigateTo(config.Page.Leaderboard, args.current);
      }
    };

    websocket.onerror = () => {
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

    ws.current = websocket;

    // When the game starts, the player gets the update first and then gets sent to this page,
    // so the initial state transfered in said update is carried out into config

    const initialState = config.getInitialPlayerState();
    setGameState(initialState);
    if (!initialState || !initialState.expires_at
      || !initialState.tries_left || !initialState.team_scores) { return; }
    setTotalWords(initialState.remaining_words_count + 1);
    expiresAt.current = initialState.expires_at;
    triesLeft.current = initialState.tries_left;
    score.current = initialState.team_scores[args.current.name];
    setAttemptsLeft(triesLeft.current);
    setCorrectCount(score.current);
  }, []);

  useEffect(() => {
    const storedArgs = config.getArgs();
    args.current = storedArgs;
    connectWebSocket();
  }, [connectWebSocket]);

  // Sets a time interval to update the timer
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeStr(formatTimeLeft(expiresAt.current));
    }, 500);

    return () => clearInterval(interval);
  }, []);

  const handleSkip = () => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action: 'skip' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    // Crucial, since most browsers do stupid stuff when submiting a form (e.g. reloading a page)
    e.preventDefault();
    if (!inputWord.trim()) return;

    setEnteredWords([...enteredWords, inputWord]);
    const str = inputWord;
    ws.current?.send(JSON.stringify({ action: 'guess', guess: str }));
    setInputWord('');
  };

  if (error) {
    return (
      <div className="quiz-container">
        <div className="error-message">{error}</div>
        {isReconnecting ? (
          <div className="reconnecting">Reconnecting...</div>
        ) : (
          <button type="button" onClick={() => config.navigateTo(config.Page.Home)} className="back-button">
            Back to Home
          </button>
        )}
      </div>
    );
  }

  if (!gameState) {
    return <div className="quiz-container">Loading...</div>;
  }

  if (args.current.name === gameState.current_master) { // Quiz-card for the game master
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#FAF6E9] dark:bg-[#1A1A1A] font-adlam text-[#3171a6]">
        <div className="text-xl mb-2">
          Words remaining:
          {' '}
          {gameState.remaining_words_count}
        </div>
        <div className="text-xl mb-6">
          {gameState.current_word !== null ? `Time left: ${timeStr}` : 'Out of words!'}
        </div>
        <StackCard word={gameState.current_word || 'Your team is out of words!'} />
        <button type="button" onClick={handleSkip} className="mt-2 bg-[#3171a6] text-white px-6 py-3 rounded-lg hover:bg-[#2c5d8f]">Skip</button>
      </div>
    );
  }

  return ( // Playing field for the player
    <div className="flex flex-col md:flex-row min-h-screen bg-[#FAF6E9] dark:bg-[#1A1A1A] p-10 font-adlam">
      <div className="bg-[#d9d9d9] rounded-lg p-6 w-full md:w-1/2 min-h-[400px] mb-6 md:mb-0">
        <h2 className="text-2xl font-bold text-[#3171a6] border-b-4 border-[#3171a6] mb-4">Entered words:</h2>
        <ul className="text-[#3171a6]">
          {enteredWords.map((word) => <li key={word}>{word}</li>)}
        </ul>
      </div>
      <div className="flex-1 flex flex-col items-center">
        <div className="flex justify-between w-full max-w-xl mb-4 text-[#3171a6] font-bold">
          <h2>
            {gameState.current_word !== null ? `Time left: ${timeStr}` : 'Out of words!'}
          </h2>
          <div>
            Correct:
            {' '}
            {correctCount}
            {' / '}
            {totalWords}
          </div>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col items-center w-full max-w-xl">
          <input
            type="text"
            placeholder="Enter a word........"
            value={inputWord}
            onChange={(e) => setInputWord(e.target.value)}
            className="w-full p-4 rounded-full bg-[#d9d9d9] text-[#3171a6] text-lg mb-4 focus:outline-none"
          />
          <button type="submit" disabled={gameState.tries_left <= 0 && gameState.current_word !== null} className="bg-[#3171a6] text-white px-8 py-2 rounded hover:bg-[#2c5d8f] disabled:opacity-50">Submit</button>
        </form>
        <span className="mt-2 text-[#3171a6]">
          Attempts left:
          {' '}
          {attemptsLeft}
        </span>
        <span className={`mt-1 text-${wrong === 'Right!' ? 'green' : 'red'}-500 font-semibold`}>{wrong}</span>
      </div>
    </div>
  );
}

export default Quiz;
