import React, { useEffect, useState } from "react";
import "../style/Lobby.css";


interface Player {
  id: string;
  name: string;
}

const Lobby: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const urlParams = new URLSearchParams(window.location.search);
  const gameCode = urlParams.get("code");
  const gameUrl = "https://localhost:3000/join_game?code=" + gameCode;



  return (
  <div className="lobby-container">
    <div className="content-wrapper">
      <div className="players-section">
        <h2>Players:</h2>
        <div className="players-list">
          {players.map((player) => (
            <div key={player.id} className="player-item">
              {player.name}
            </div>
          ))}
        </div>
      </div>

      <div className="url-center-section">
        <h3>Url:</h3>
        <div className="url-box"><strong style={{ color: "#3171a6" }}></strong> {gameUrl}</div>
        <h3>Code:</h3>
        <div className="code-box"><strong style={{ color: "#3171a6" }}></strong> {gameCode}</div>
      </div>
      <div className="qr-section">
        <h3>QR-code:</h3>
        <img
          src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(
            gameUrl
          )}`}
          alt="QR Code"
        />
      </div>
    </div>

    <button className="create-button">Start game</button>
  </div>
);

};

export default Lobby;
