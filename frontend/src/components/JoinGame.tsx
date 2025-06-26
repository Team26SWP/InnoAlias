import React, { useEffect, useState, useRef } from "react";
import '../style/JoinGame.css'
import * as Config from './Config';

const JoinGame: React.FC = () => {
  const urlParams = new URLSearchParams(window.location.search);

  const [playerName, setPlayerName] = useState('');
  const [manualCode, setGameCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [socketOpen, setSocketOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
    const socketRef = useRef<WebSocket | null>(null);


  const codeFromUrl = urlParams.get("code")?.toUpperCase();
  const gameCode = codeFromUrl || manualCode;

  const validatePlayerName = (name: string): string | null => {
    // no need (max/min lenght in html)
    /*if (name.length < 2) {return 'Name must be at least 2 characters long';}
    if (name.length > 20) {return 'Name must be less than 20 characters';}*/
    if (!/^[a-zA-Z\s-]+$/.test(name)) { return 'Name can only contain letters, spaces'; }
    return null;
  };

  const validateGameCode = (code: string): string | null => {
    // no need (max lenght in html)
    // if (code.length !== 6) {return 'Game code must be 6 characters long';}
    if (!/^[A-Z0-9]+$/.test(code)) { return 'Game code can only contain uppercase letters and numbers'; }
    return null;
  };

  const handleJoinGame = async (e: React.FormEvent) => {
    e.preventDefault();

    const nameError = validatePlayerName(playerName);
    const codeError = validateGameCode(gameCode);

    if (nameError || codeError) {
      setError(nameError || codeError);
      return;
    }

    setIsLoading(true);
    setError(null);
    
    const socket = Config.connectSocketPlayer(playerName, gameCode);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('Player socket opened');
      setSocketOpen(true);
      Config.navigateTo(Config.Page.Lobby, { name: playerName, code: gameCode, isHost: false });
    };

    socket.onerror = (err) => {
      console.error('Socket error', err);
      setError('Failed to connect to the game. Please check the code and try again.');
      setIsLoading(false);
    };

    socket.onclose = () => {
      if (!socketOpen) {
        setError('Connection closed before joining.');
        setIsLoading(false);
      }
    };

  }


  return (
    <div className="join-game-container">
      <h1>Join Game</h1>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleJoinGame} className="join-form">
        <div className="form-group">
          <label htmlFor="playerName">Your Name</label>
          <input
            id="playerName"
            type="text"
            placeholder="Enter your name"
            value={playerName}
            onChange={(e) => {
              setPlayerName(e.target.value);
              setError(null);
            }}
            required
            disabled={isLoading}
            minLength={2}
            maxLength={30}
          />
        </div>

        {!urlParams.get('code') && (
          <div className="form-group">
            <label htmlFor="gameCode">Game Code</label>
            <input
              id="gameCode"
              type="text"
              placeholder="Enter game code"
              value={gameCode}
              onChange={(e) => {
                setGameCode(e.target.value.toUpperCase());
                setError(null);
              }}
              required
              disabled={isLoading}
              maxLength={6}
              pattern="[A-Z0-9]{6}"
            />
          </div>
        )}
        <button
          type="submit"
          className={`join-button`}
          disabled={isLoading}
        >
          {socketOpen ? 'Joining Game...' : 'Join Game'}
        </button>
      </form>
    </div>
  );
};
export default JoinGame;