import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import '../style/JoinGame.css'


const API_URL = '/api';

const JoinGame: React.FC = () => {
    const navigate = useNavigate();

    const { code:urlCode } = useParams();
    
    const [playerName, setPlayerName] = useState('');
    const [manualCode, setGameCode] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const gameCode = urlCode?.toUpperCase() || manualCode;
    
    const validatePlayerName = (name: string): string | null => {
        if (name.length < 2) {return 'Name must be at least 2 characters long';}
        if (name.length > 20) {return 'Name must be less than 20 characters';}
        if (!/^[a-zA-Z0-9\s-]+$/.test(name)) {return 'Name can only contain letters, numbers, spaces, and hyphens';}
        return null;
    };

    const validateGameCode = (code: string): string | null => {
        if (code.length !== 6) {return 'Game code must be 6 characters long';}
        if (!/^[A-Z0-9]+$/.test(code)) {return 'Game code can only contain uppercase letters and numbers';}
        return null;
    };
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const nameError = validatePlayerName(playerName);
        const codeError = validateGameCode(gameCode);
        
        if (nameError) {
            setError(nameError);
            return;
        }

        if (codeError) {
            setError(codeError);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_URL}/join/game`, {
                method: 'POST',
                headers: {
                'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    playerName,
                    gameCode
                })
            });

            if (!response.ok) {
                throw new Error('Failed to join game');
            }

            const data = await response.json();
            navigate(`/game/${data.id}`);
        } catch (err) {
            setError('Failed to join game. Please try again.');
            console.error('Error joining game:', err);
        } finally {
            setIsLoading(false);
        }
    };
    
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
                        maxLength={20}
                    />
                </div>
                
                {!urlCode && (
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
                    className="join-button"
                    disabled={isLoading}
                >
                    {isLoading ? 'Joining Game...' : 'Join Game'}
                </button>
            </form>
        </div>
    );
};

export default JoinGame;