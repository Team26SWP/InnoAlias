import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import '../style/JoinGame.css'

/**
 * JoinGame Component
 * 
 * This component allows players to join an existing game by:
 * 1. Entering their name
 * 2. Providing a game code
 * 
 * The component handles form submission and navigation to the game lobby
 * upon successful validation of the input.
 */
const JoinGame: React.FC = () => {
    // Hook for programmatic navigation between routes
    const navigate = useNavigate();
    
    // State to store the player's name
    const [playerName, setPlayerName] = useState('');
    // State to store the game code entered by the player
    const [gameCode, setGameCode] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    
    /**
     * Validates the player name
     * @param name - The name to validate
     * @returns string | null - Error message if invalid, null if valid
     */
    const validatePlayerName = (name: string): string | null => {
        if (name.length < 2) {
            return 'Name must be at least 2 characters long';
        }
        if (name.length > 20) {
            return 'Name must be less than 20 characters';
        }
        if (!/^[a-zA-Z0-9\s-]+$/.test(name)) {
            return 'Name can only contain letters, numbers, spaces, and hyphens';
        }
        return null;
    };

    /**
     * Validates the game code
     * @param code - The code to validate
     * @returns string | null - Error message if invalid, null if valid
     */
    const validateGameCode = (code: string): string | null => {
        if (code.length !== 6) {
            return 'Game code must be 6 characters long';
        }
        if (!/^[A-Z0-9]+$/.test(code)) {
            return 'Game code can only contain uppercase letters and numbers';
        }
        return null;
    };
    
    /**
     * Handles the form submission when joining a game
     * Validates that both player name and game code are provided
     * Navigates to the game lobby if validation passes
     * @param e - Form event object
     */
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        // Validate inputs
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
            // Here we would typically send the game code and player name to the backend
            // For now, we'll just navigate to the lobby with the provided game code
            navigate(`/lobby/${gameCode}`);
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
            {/* Form for joining an existing game */}
            <form onSubmit={handleSubmit} className="join-form">
                {/* Player name input field */}
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

                {/* Game code input field */}
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

                {/* Submit button to join the game */}
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