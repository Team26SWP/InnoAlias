import React from "react";
import "../style/Leaderboard.css";

interface Player {
  name: string;
  score: number;
}

const Leaderboard: React.FC = () => {
  const players: Player[] = [
    { name: "Player 1", score: 5000 },
    { name: "Player 2", score: 5000 },
    { name: "Player 3", score: 5000 },
    { name: "Player 4", score: 5000 },
    { name: "Player 5", score: 5000 }
  ];

  const saveDeck = () => {
    var words: string[]; // deck words from WS go here
    words = [];
    const deckName = prompt("Please, input the name of the deck");
    if (deckName) document.cookie = deckName + "=[" + words.join(";") + "]";
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
        <button className="button light">Export Leaderboard</button>
        <button className="button primary">Back to main</button>
        <button className="button light" onClick={saveDeck}>Save Deck</button>
      </div>
    </div>
  );
};

export default Leaderboard;
