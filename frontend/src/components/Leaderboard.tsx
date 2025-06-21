import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "../style/Leaderboard.css";

import socketConfig from "./socketConfig";
const HTTP_URL = socketConfig.HTTP_URL;

interface Player {
  name: string;
  score: number;
}

const Leaderboard: React.FC = () => {
  var [players, setPlayers] = useState<Player[]>([]);

  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get("code");

  const { gameId } = useParams<{ gameId: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();


  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const response = await fetch(
          `${HTTP_URL}/game/leaderboard/${code}`
        );
        if (!response.ok) {
          if (response.status === 404) {
            setError("Game not found.");
          } else {
            setError("Failed to fetch leaderboard.");
          }
          throw new Error("Failed to fetch leaderboard");
        }
        const scores = await response.json();
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

    if (code) {
      fetchLeaderboard();
    }
  }, [code]);

  const saveDeck = async () => {
    const response = await fetch(`${HTTP_URL}/game/deck/${code}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await response.json();
    var words: string[] = data.deck;
    const deckName = prompt("Please, input the name of the deck");
    if (deckName) document.cookie = deckName + "=[" + words.join(",") + "]";
  }

  const toMain = () => {
    navigate("/");
  } 

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
        <button className="button primary" onClick={ toMain }>Back to main</button>
        <button className="button light" onClick={saveDeck}>Save Deck</button>
      </div>
    </div>
  );
};

// <button className="button light">Export Leaderboard</button>

export default Leaderboard;
