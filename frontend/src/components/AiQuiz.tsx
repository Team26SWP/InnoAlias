import { useState, useEffect } from 'react';
import * as config from './config';

function AiQuiz() {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [message, setMessage] = useState<string>('Click "Start" when you are ready!');
  const [guessMessage, setGuessMessage] = useState<string>('');
  const [gameState, setGameState] = useState<config.AiGameState | null>(null);
  const [timeStr, setTimeStr] = useState<string>('Loading...');
  const [guess, setGuess] = useState<string>('');
  const [guessing, setGuessing] = useState(false);
  const [loading, setLoading] = useState(false);

  const formatTimeLeft = (endTime: string): string => {
    const now = new Date();
    const expires = new Date(endTime);
    const diff = expires.getTime() - now.getTime();

    if (diff <= 0) return 'Time\'s up!';

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const handleSkip = () => {
    setGuessMessage(`Guessed word was: ${gameState?.current_word}`);
    setGuessing(true);
    socket?.send(JSON.stringify({ action: 'skip' }));
  };

  const handleStart = () => {
    setLoading(true);
    socket?.send(JSON.stringify({ action: 'start_game' }));
  };

  const handleGuess = (e: React.FormEvent) => {
    e.preventDefault();
    if (guess.trim()) {
      setGuessing(true);
      if (guess.toLowerCase() === gameState?.current_word?.toLowerCase()) {
        setGuessMessage(`Guess ${guess} was correct!`);
      } else {
        setGuessMessage(`Guess ${guess} was wrong!`);
      }
      socket?.send(JSON.stringify({ action: 'guess', guess }));
      setGuess('');
    }
  };

  const getTextColorClass = (text: string) => {
    if (text.includes('correct')) return 'text-green-500';
    if (text.includes('wrong')) return 'text-red-500';
    return 'text-[#3171a6]';
  };

  useEffect(() => {
    const initialState: config.AiGameState | null = config.getInitialAiState();
    if (!initialState) { return; }
    setGameState(initialState);
  }, []);

  useEffect(() => {
    const stopGame = (data: config.AiGameState) => {
      if (!gameState) { return; }
      alert(`You have guessed ${data.score} out of ${data.deck.length - data.remaining_words.length}!`);
      config.navigateTo(config.Page.Home);
    };
    const ws = config.connectSocketAi(config.getArgs().code);
    setSocket(ws);
    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.game_state === 'finished') {
        stopGame(data);
        return;
      }
      if (gameState?.current_word && data.expires_at !== gameState?.expires_at
        && gameState.score === data.score) {
        setGuessMessage(`Guessed word was: ${gameState?.current_word}`);
      }
      setGameState(data);
      const clue = data.clues[data.clues.length - 1];
      setMessage(clue);
      setGuessing(false);
      setLoading(false);
    };
  }, [gameState, gameState?.expires_at, gameState?.current_word, gameState?.score]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (!gameState || !gameState.expires_at) { return; }
      setTimeStr(formatTimeLeft(gameState?.expires_at));
    }, 500);

    return () => clearInterval(interval);
  }, [gameState]);

  if (!gameState) {
    return <div>Loading...</div>;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#FAF6E9] dark:bg-[#1A1A1A] font-adlam text-[#3171a6]">
      <div className="text-xl mb-2">
        Words remaining:
        {' '}
        {gameState.remaining_words.length}
      </div>
      <div className="text-xl mb-2">
        {`Score: ${gameState.score}/${gameState.deck.length - gameState.remaining_words.length - (gameState.game_state === 'pending' ? 0 : 1)}`}
      </div>
      <div className="text-xl mb-6">
        {gameState.current_word !== null ? `Time left: ${timeStr}` : 'Waiting...'}
      </div>
      <div className="text-4xl font-bold bg-gray-200 px-12 py-8 rounded-xl shadow mb-4">
        {guessing ? 'Loading...' : message}
      </div>
      <div>
        {gameState.game_state !== 'pending' ? (
          <form onSubmit={handleGuess}>
            <input
              type="text"
              onChange={(e) => { setGuess(e.target.value); }}
              value={guess}
              className="p-4 rounded-full bg-gray-200 text-[#3171a6] text-lg mb-4 focus:outline-none"
              disabled={guessing}
            />
            <button type="submit" disabled={guessing} className="ml-2 mt-2 bg-[#3171a6] text-white px-6 py-3 rounded-lg hover:bg-[#2c5d8f]">{guessing ? 'Loading...' : 'Guess'}</button>
            <button type="button" onClick={handleSkip} className="ml-2 mt-2 bg-[#3171a6] text-white px-6 py-3 rounded-lg hover:bg-[#2c5d8f]">Skip</button>
          </form>
        ) : (
          <button type="button" disabled={loading} onClick={handleStart} className="mt-2 bg-[#3171a6] text-white px-6 py-3 rounded-lg hover:bg-[#2c5d8f]">{loading ? 'Loading...' : 'Start'}</button>
        )}
      </div>
      <div className={`text-xl mt-2 ${getTextColorClass(guessMessage)}`}>
        {guessMessage}
      </div>
      <button type="button" onClick={() => { config.navigateTo(config.Page.Home); }} className="mt-2 bg-[#3171a6] text-white px-6 py-3 rounded-lg hover:bg-[#2c5d8f]">Quit</button>
    </div>
  );
}

export default AiQuiz;
