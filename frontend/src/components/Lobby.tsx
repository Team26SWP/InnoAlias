import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../style/Lobby.css";

import socketConfig from "./socketConfig";

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
  const name = urlParams.get("name");
  const isHost = urlParams.get("host") === "true";
  const navigate = useNavigate();

  useEffect(() => {
    if (isHost && gameCode && name) {
      const ws = socketConfig.connectSocketHost(name, gameCode);
      setSocket(ws);
      ws.onopen = () => { console.log("host connection successful"); }
    }
    else if (!isHost && gameCode && name) {
      const ws = socketConfig.connectSocketPlayer(name, gameCode);
      ws.onopen = () => { console.log("player connection successful"); }
      ws.onmessage = (message) => {
        const data = JSON.parse(message.data);
        if (data.state === "in_progress") {
          navigate(`/game/${gameCode}?name=${name}&host=false`, { state: {game_state: data} });
        }
      }
      setSocket(ws);
    }
  }, [gameCode, name, isHost, navigate]);

  const handleStartGame = () => {
    socket?.send(JSON.stringify({ action: "start" }));
    navigate(`/game/${gameCode}?name=${name}&host=true`);
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

      {isHost ? <button className="create-button" onClick={handleStartGame}>Start game</button> : <div></div>}
  </div>
);

};

export default Lobby;
