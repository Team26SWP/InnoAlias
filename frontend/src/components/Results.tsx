import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../style/Results.css';

/**
 * Interface defining the structure of a player's score
 * @property id - Unique identifier for the player
 * @property name - Player's display name
 * @property score - Player's final score
 * @property rank - Player's final ranking
 */
interface PlayerScore {
  id: string;
  name: string;
  score: number;
  rank: number;
}

// Mock data for testing the results display
// TODO: Replace with actual API call to fetch real results
const mockResults: PlayerScore[] = [
  { id: '1', name: 'Player 1', score: 8, rank: 1 },
  { id: '2', name: 'Player 2', score: 6, rank: 2 },
  { id: '3', name: 'Player 3', score: 4, rank: 3 },
];

/**
 * Results Component
 * 
 * This component displays the final game results, including:
 * 1. Top 3 players with special highlighting
 * 2. Complete list of all players and their scores
 * 3. Option to play again
 * 
 * Currently uses mock data, but should be updated to fetch real results
 * from the backend when implemented.
 */
const Results: React.FC = () => {
  // Get game ID from URL parameters
  const { gameId } = useParams<{ gameId: string }>();
  // Hook for programmatic navigation
  const navigate = useNavigate();

  /**
   * Handles navigation back to home page when "Play Again" is clicked
   */
  const handlePlayAgain = () => {
    navigate('/');
  };

  return (
    <div className="results-container">
      <h1>Game Results</h1>
      
      <div className="results-card">
        {/* Top 3 players section with special styling */}
        <div className="top-players">
          {mockResults.slice(0, 3).map((player) => (
            <div key={player.id} className={`player-result rank-${player.rank}`}>
              <div className="rank">{player.rank}</div>
              <div className="player-info">
                <div className="player-name">{player.name}</div>
                <div className="player-score">{player.score} points</div>
              </div>
            </div>
          ))}
        </div>

        {/* Complete list of all players */}
        <div className="all-players">
          <h2>All Players</h2>
          <div className="players-list">
            {mockResults.map((player) => (
              <div key={player.id} className="player-row">
                <span className="player-rank">#{player.rank}</span>
                <span className="player-name">{player.name}</span>
                <span className="player-score">{player.score} points</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action buttons section */}
      <div className="results-actions">
        <button className="play-again-button" onClick={handlePlayAgain}>
          Play Again
        </button>
      </div>
    </div>
  );
};

export default Results; 