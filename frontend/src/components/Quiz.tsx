import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../style/Quiz.css';

/**
 * Interface defining the structure of the game state
 * @property current_word - The word currently being played
 * @property expires_at - Timestamp when the current word expires
 * @property remaining_words_count - Number of words left in the game
 * @property state - Current state of the game (in_progress or finished)
 */
interface GameState {
  current_word: string | null;
  expires_at: string | null;
  remaining_words_count: number;
  state: 'in_progress' | 'finished';
}

// WebSocket server URL for real-time game updates
const API_URL = 'ws://212.113.122.8/';

/**
 * Quiz Component
 * 
 * This component handles the main gameplay experience:
 * 1. Establishes WebSocket connection for real-time game updates
 * 2. Displays current word and game progress
 * 3. Handles word skipping
 * 4. Manages game state and error handling
 * 5. Navigates to results page when game is finished
 */
const Quiz: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  /**
   * Formats the remaining time in a user-friendly way
   * @param expiresAt - The expiration timestamp
   * @returns string - Formatted time string
   */
  const formatTimeLeft = (expiresAt: string): string => {
    const now = new Date().getTime();
    const expires = new Date(expiresAt).getTime();
    const diff = expires - now;
    
    if (diff <= 0) return 'Time\'s up!';
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  /**
   * Establishes WebSocket connection with reconnection logic
   */
  const connectWebSocket = useCallback(() => {
    if (!gameId) return;

    const websocket = new WebSocket(`${API_URL}/game/${gameId}`);

    websocket.onopen = () => {
      console.log('Connected to game server');
      setIsReconnecting(false);
      setError(null);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setGameState(data);

      if (data.state === 'finished') {
        navigate(`/`);
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
/*        
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 3000); */
      }
    };

    setWs(websocket);
  }, [gameId, navigate]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket]); 

  const handleSkip = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'skip' }));
    }
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

  return (
    <div className="quiz-container">
      <div className="question-card">
        <div className="game-info">
          <div className="remaining-words">
            Words remaining: {gameState.remaining_words_count}
          </div>
          {gameState.expires_at && (
            <div className="timer">
              Time left: {formatTimeLeft(gameState.expires_at)}
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
};

export default Quiz; 