import React, { useEffect, useState } from "react";
import "../style/Lobby.css";

import * as Config from './Config';

interface Player {
    name: string;
    score: number;
}

const Lobby: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [socket, setSocket] = useState<WebSocket>();
  const urlParams = new URLSearchParams(window.location.search);
  const gameCode = urlParams.get("code");
  const gameUrl = "http://" + window.location.host + "/join_game?code=" + gameCode;
  const name = urlParams.get("name");
  const isHost = urlParams.get("host") === "true";

  useEffect(() => {
    if (!gameCode || !name) return;

    if (isHost) {
      const ws = Config.connectSocketHost(name, gameCode);
      setSocket(ws);
      ws.onopen = () => { console.log("host connection successful"); };
      ws.onmessage = (message) => {
          const data = JSON.parse(message.data);
          const suppArray = Object.keys(data.scores).map((key) => ({ name: key, score: data.scores[key] }));
        if (data.scores) {
          setPlayers(suppArray);
        }
        if (data.state === "in_progress") {
          //navigate(`/game/${gameCode}?name=${name}&host=false`, { state: {game_state: data} });
        }
      };
    }
    else {
      const ws = Config.connectSocketPlayer(name, gameCode);
      setSocket(ws);
      ws.onopen = () => { console.log("player connection successful"); };
        ws.onmessage = (message) => {
            const data = JSON.parse(message.data);
            const suppArray = Object.keys(data.scores).map((key) => ({ name: key, score: data.scores[key] }));
            if (data.scores) {
                setPlayers(suppArray);
            }
        
        if (data.state === "in_progress") {
          //navigate(`/game/${gameCode}?name=${name}&host=false`, { state: {game_state: data} });
        }
      };
    }
  }, [gameCode, name, isHost, /*navigate*/]);

  const handleStartGame = () => {
    socket?.send(JSON.stringify({ action: "start" }));
    //navigate(`/game/${gameCode}?name=${name}&host=true`);
  }

  return (
  <div className="lobby-container">
    <div className="content-wrapper">
      <div className="players-section"> 
        <h2>Players:</h2>
        <div className="players-list">
          {players.map((player, i) => (
            <div key={i} className="player-item">
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
