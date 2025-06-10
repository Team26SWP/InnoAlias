import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import '../style/JoinGame.css'

const JoinGame: React.FC = () => {
    const navigate = useNavigate();
    const [playerName, setPlayerName] = useState('');
    const [gameCode, setGameCode] = useState('');
    
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (playerName && gameCode) {
        // Here we would typically send the game code and player name to the backend
        // For now, we'll just navigate to the lobby with the provided game code
        navigate(`/lobby/${gameCode}`);
        }
    };
    
    return (
        <div className="join-game-container">
        <h1>Join Game</h1>
        <form onSubmit={handleSubmit} className="join-form">
            <div className="form-group">
                <label htmlFor="playerName">Your Name</label>
                <input
                id="playerName"
                type="text"
                placeholder="Enter your name"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                required
                />
            </div>

            <div className="form-group">
                <label htmlFor="gameCode">Game Code</label>
                <input
                id="gameCode"
                type="text"
                placeholder="Enter game code"
                value={gameCode}
                onChange={(e) => setGameCode(e.target.value)}
                required
                />
            </div>

            <button type="submit" className="join-button">
            Join Game
            </button>
        </form>
        </div>
    );
};

export default JoinGame;