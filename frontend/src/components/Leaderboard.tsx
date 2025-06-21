import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "../style/Leaderboard.css";

interface Player {
  name: string;
  score: number;
}

const Leaderboard: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const response = await fetch(
          `http://217.199.253.164/api/game/leaderboard/${gameId}`
        );
        if (!response.ok) {
          if (response.status === 404) {
            setError("Game not found.");
          } else {
            setError("Failed to fetch leaderboard.");
          }
          throw new Error("Failed to fetch leaderboard");
        }
        const data = await response.json();
        const scores = data.scores;
        const formattedPlayers: Player[] = Object.keys(scores).map((key) => ({
            name: key,
            score: scores[key],
          }));
        
        formattedPlayers.sort((a, b) => b.score - a.score);

        setPlayers(formattedPlayers);
      } catch (err) {
        setError("An error occurred while fetching the leaderboard.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (gameId) {
      fetchLeaderboard();
    }
  }, [gameId]);

  const handleBackToMain = () => {
    navigate("/");
  };

  if (loading) {
    return <div className="leaderboard-container">Loading...</div>;
  }

  if (error) {
    return <div className="leaderboard-container">Error: {error}</div>;
  }

  return (
    <div className="leaderboard-container">
      <h1 className="leaderboard-title">Leaderboard</h1>
      <div className="leaderboard-table">
        {players.map((player, index) => (
          <div className="leaderboard-row" key={index}>
            <div className="leaderboard-rank">{index + 1}.</div>
            <div className="leaderboard-name">{player.name}</div>
            <div className="leaderboard-score">{player.score}</div>
          </div>
        ))}
      </div>
      <div className="leaderboard-buttons">
        <button className="button primary" onClick={handleBackToMain}>
          Back to main
        </button>
      </div>
    </div>
  );
};

export default Leaderboard;
