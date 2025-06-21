import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
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

  const location = useLocation();
  const navigate = useNavigate();


  useEffect(() => {
    const scores: { [name: string]: number } = location.state.scores;
    const playerNames: string[] = Object.keys(scores);
    const supplementaryArray: Player[] = [];
    for (var i = 0; i < playerNames.length; i++) {
      supplementaryArray.push({ name: playerNames[i], score: scores[playerNames[i]] });
    }
    supplementaryArray.sort((a, b) => b.score - a.score);
    setPlayers(supplementaryArray);
  }, [location.state.scores])

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
        <button className="button primary" onClick={ toMain }>Back to main</button>
        <button className="button light" onClick={saveDeck}>Save Deck</button>
      </div>
    </div>
  );
};

export default Leaderboard;
