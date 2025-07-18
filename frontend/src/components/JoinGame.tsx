import React, {
  useEffect,
  useState,
  useRef,
  useCallback,
} from 'react';
import * as config from './config';

export function JoinGame() {
  const urlParams = new URLSearchParams(window.location.search);
  const [playerName, setPlayerName] = useState('');
  const [manualCode, setGameCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [socketOpen, setSocketOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const codeFromUrl = urlParams.get('code')?.toUpperCase();
  const gameCode = codeFromUrl || manualCode;

  const validateGameCode = (code: string): string | null => {
    // no need (max lenght in html)
    // if (code.length !== 6) {return 'Game code must be 6 characters long';}
    if (!/^[A-Z0-9]+$/.test(code)) { return 'Game code can only contain uppercase letters and numbers'; }
    return null;
  };

  const handleJoinGame = useCallback(async (
    e: React.FormEvent | null = null,
    name: string = playerName,
  ) => {
    if (e) {
      e.preventDefault();
    }

    const codeError = validateGameCode(gameCode);

    if (codeError) {
      setError(codeError);
      return;
    }

    setIsLoading(true);
    setError(null);

    const socket = config.connectSocketPlayer(name, gameCode);
    socketRef.current = socket;

    socket.onopen = () => {
      setSocketOpen(true);
      config.navigateTo(config.Page.Lobby, { name, code: gameCode, isHost: false });
    };

    socket.onerror = () => {
      setError('Failed to connect to the game. Please check the code and try again.');
      setIsLoading(false);
    };

    socket.onclose = () => {
      if (!socketOpen) {
        setError('Connection closed before joining.');
        setIsLoading(false);
      }
    };
  }, [gameCode, playerName, socketOpen]);

  useEffect(() => {
    const profile = config.getProfile();
    if (profile) {
      setPlayerName(profile.name);
    }
    if (codeFromUrl && profile) {
      window.history.pushState({}, document.title, window.location.pathname);
      handleJoinGame(null, profile.name);
    }
  }, [codeFromUrl, handleJoinGame]);

  return (
    <div className="min-h-screen bg-[#FAF6E9] dark:bg-[#1A1A1A] flex flex-col items-center justify-center px-6 py-12">
      <button
        type="button"
        onClick={() => config.navigateTo(config.Page.Home)}
        className="absolute top-4 text-xl left-4 text-[#1E6DB9] hover:underline"
      >
        ←Back to main
      </button>
      <h1 className="text-5xl font-bold text-[#1E6DB9] mb-10">Join Game</h1>
      <form onSubmit={handleJoinGame} className="w-full max-w-lg flex flex-col items-center gap-6">
        <div className="w-full">
          <label htmlFor="code" className="block text-2xl font-medium text-[#1E6DB9] mb-3 ml-4">
            Code
            <input
              id="code"
              type="text"
              placeholder="ENTER THE CODE"
              value={gameCode}
              onChange={(e) => {
                setGameCode(e.target.value.toUpperCase());
                setError(null);
              }}
              disabled={!!codeFromUrl}
              className="w-full bg-[#D9D9D9] placeholder-[#7d7d7d] text-[#1E6DB9] px-6 py-4 rounded-full text-lg outline-none"
              maxLength={6}
              required
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="mt-6 bg-[#1E6DB9] text-[#FAF6E9] px-8 py-3 rounded-lg text-lg font-medium hover:opacity-90 transition disabled:opacity-50"
        >
          {isLoading ? 'Connecting...' : 'Connect'}
        </button>

        {/* Error Message */}
        {error && <p className="text-red-600 mt-2">{error}</p>}
      </form>
    </div>
  );
}

export default JoinGame;
