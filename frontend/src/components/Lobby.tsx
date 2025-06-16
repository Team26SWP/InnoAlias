import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import "../style/Lobby.css";

/**
 * Interface defining the structure of a player in the lobby
 * @property id - Unique identifier for the player
 * @property name - Player's display name
 * @property isHost - Whether the player is the game host
 */
interface Player {
  id: string;
  name: string;
  isHost: boolean;
}

/**
 * Interface defining the structure of the lobby state
 * @property players - List of players in the lobby
 * @property gameId - Unique identifier for the game
 * @property isHost - Whether the current user is the host
 */
interface LobbyState {
  players: Player[];
  gameId: string;
  isHost: boolean;
}

// WebSocket server URL for real-time lobby updates
const API_URL = 'ws://localhost:8000/api';

/**
 * Lobby Component
 * 
 * This component handles the game lobby functionality:
 * 1. Establishes WebSocket connection for real-time player updates
 * 2. Displays list of players who have joined
 * 3. Allows the host to start the game
 * 4. Shows game code for players to share
 * 5. Handles connection errors and game start events
 */
const Lobby: React.FC = () => {
  // Get game ID from URL parameters
  const { gameId } = useParams<{ gameId: string }>();
  // Hook for programmatic navigation
  const navigate = useNavigate();
  // State to store lobby information
  const [lobbyState, setLobbyState] = useState<LobbyState | null>(null);
  // State to handle error messages
  const [error, setError] = useState<string | null>(null);
  // State to store WebSocket connection
  const [ws, setWs] = useState<WebSocket | null>(null);

  /**
   * Effect hook to establish and manage WebSocket connection
   * Handles connection events, message processing, and cleanup
   */
  useEffect(() => {
    if (!gameId) return;

    const websocket = new WebSocket(`${API_URL}/lobby/${gameId}`);

    // Handle successful connection
    websocket.onopen = () => {
      console.log('Connected to lobby server');
    };

    // Process incoming lobby updates
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLobbyState(data);

      // Navigate to game page when game starts
      if (data.gameStarted) {
        navigate(`/game/${gameId}`);
      }
    };

    // Handle WebSocket errors
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error. Please try again.');
    };

    // Handle WebSocket connection closure
    websocket.onclose = (event) => {
      if (event.code === 1011) {
        setError('Game not found');
      } else {
        setError('Connection closed. Please try again.');
      }
    };

    setWs(websocket);

    // Cleanup: close WebSocket connection on component unmount
    return () => {
      websocket.close();
    };
  }, [gameId, navigate]);

  /**
   * Handles starting the game
   * Sends start game action to the server via WebSocket
   */
  const handleStartGame = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'start_game' }));
    }
  };

  // Display error message and return button if there's an error
  if (error) {
    return (
      <div className="lobby-container">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/')} className="back-button">
          Back to Home
        </button>
      </div>
    );
  }

  // Show loading state while lobby state is being fetched
  if (!lobbyState) {
    return <div className="lobby-container">Loading...</div>;
  }

  return (
    <div className="lobby-container">
      <div className="lobby-card">
        <h1>Game Lobby</h1>
        
        {/* Game code display */}
        <div className="game-code">
          <h2>Game Code:</h2>
          <div className="code">{gameId}</div>
          <p>Share this code with your friends to join the game!</p>
        </div>

        {/* Players list */}
        <div className="players-section">
          <h2>Players ({lobbyState.players.length})</h2>
          <div className="players-list">
            {lobbyState.players.map((player) => (
              <div key={player.id} className={`player-item ${player.isHost ? 'host' : ''}`}>
                <span className="player-name">{player.name}</span>
                {player.isHost && <span className="host-badge">Host</span>}
              </div>
            ))}
          </div>
        </div>

        {/* Start game button (only visible to host) */}
        {lobbyState.isHost && (
          <div className="lobby-actions">
            <button 
              onClick={handleStartGame}
              disabled={lobbyState.players.length < 2}
              className="start-game-button"
            >
              Start Game
            </button>
            {lobbyState.players.length < 2 && (
              <p className="warning">Need at least 2 players to start</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Lobby;

