import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../style/Lobby.css";

import socketConfig from "./socketConfig";

const WS_URL = "ws://localhost:8000/api"

interface Player {
  id: string;
  name: string;
}

const Lobby: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [socket, setSocket] = useState<WebSocket>();
  const urlParams = new URLSearchParams(window.location.search);
  const gameCode = urlParams.get("code");
  const gameUrl = "https://localhost:3000/join_game?code=" + gameCode;
  const hostName = urlParams.get("host");
  const navigate = useNavigate();

  useEffect(() => {
    if (hostName && gameCode) {
      const ws = socketConfig.connectSocketHost(hostName, gameCode);
      setSocket(ws);
      ws.onopen = () => { console.log("connection successful"); }
    }
  }, [gameCode, hostName]);

  const handleStartGame = () => {
    socket?.send(JSON.stringify({ action: "start" }));
    navigate(`/game/${gameCode}`, { state: {webSocket: socket} });
  }

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

      {hostName ? <button className="create-button" onClick={handleStartGame}>Start game</button> : <div></div>}
  </div>
);

};

export default Lobby;
