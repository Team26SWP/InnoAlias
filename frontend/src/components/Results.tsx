import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../style/Results.css';

interface PlayerScore {
  id: string;
  name: string;
  score: number;
  rank: number;
}

const mockResults: PlayerScore[] = [
  { id: '1', name: 'Player 1', score: 8, rank: 1 },
  { id: '2', name: 'Player 2', score: 6, rank: 2 },
  { id: '3', name: 'Player 3', score: 4, rank: 3 },
];

const Results: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();

  const handlePlayAgain = () => {
    navigate('/');
  };

  return (
    <div className="results-container">
      <h1>Game Results</h1>
      
      <div className="results-card">
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

      <div className="results-actions">
        <button className="play-again-button" onClick={handlePlayAgain}>
          Play Again
        </button>
      </div>
    </div>
  );
};

export default Results; 