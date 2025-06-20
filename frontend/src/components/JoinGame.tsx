import React, { useEffect, useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import '../style/JoinGame.css'

import socketConfig from "./socketConfig";

const JoinGame: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [playerName, setPlayerName] = useState('');
  const [manualCode, setGameCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [socketOpen, setSocketOpen] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const codeFromUrl = searchParams.get("code")?.toUpperCase();
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const nameError = validatePlayerName(playerName);
    const codeError = validateGameCode(gameCode);

    if (nameError || codeError) {
      setError(nameError || codeError);
      return;
    }

    setIsLoading(true);
    setError(null);
    const ws = socketConfig.connectSocketPlayer(playerName, gameCode);
    socketRef.current = ws;

    ws.onopen = () => {
      setSocketOpen(true);
      console.log("Player connected succesfully");
      navigate(`/lobby?code=${gameCode}&name=${playerName}&host=false`);
    };

    ws.onerror = () => {
      setError("Failed to connect to game. Check your code and try again.");
      setIsLoading(false);
    };
    ws.onclose = () => {
      if (!socketOpen) {
        setError("Connection closed before joining. Is the game running?");
        setIsLoading(false);
      }
    };
  };

  useEffect(() => {
    return () => {
      socketRef.current?.close();
    };
  }, []);

  return (
    <div className="join-game-container">
      <h1>Join Game</h1>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit} className="join-form">
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

        {!searchParams.get('code') && (
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