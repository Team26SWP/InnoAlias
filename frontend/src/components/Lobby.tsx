import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import socketConfig from "./config";

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
  const navigate = useNavigate();

  useEffect(() => {
    if (!gameCode || !name) return;

    if (isHost) {
      const ws = socketConfig.connectSocketHost(name, gameCode);
      setSocket(ws);
      ws.onopen = () => { console.log("host connection successful"); };
      ws.onmessage = (message) => {
          const data = JSON.parse(message.data);
          const suppArray = Object.keys(data.scores).map((key) => ({ name: key, score: data.scores[key] }));
        if (data.scores) {
          setPlayers(suppArray);
        }
        if (data.state === "in_progress") {
          navigate(`/game/${gameCode}?name=${name}&host=false`, { state: {game_state: data} });
        }
      };
    }
    else {
      const ws = socketConfig.connectSocketPlayer(name, gameCode);
      setSocket(ws);
      ws.onopen = () => { console.log("player connection successful"); };
        ws.onmessage = (message) => {
            const data = JSON.parse(message.data);
            const suppArray = Object.keys(data.scores).map((key) => ({ name: key, score: data.scores[key] }));
            if (data.scores) {
                setPlayers(suppArray);
            }
        
        if (data.state === "in_progress") {
          navigate(`/game/${gameCode}?name=${name}&host=false`, { state: {game_state: data} });
        }
      };
    }
  }, [gameCode, name, isHost, navigate]);

  const handleStartGame = () => {
    socket?.send(JSON.stringify({ action: "start" }));
    navigate(`/game/${gameCode}?name=${name}&host=true`);
  }

  return (
    <div className="min-h-screen pt-32 px-9 bg-[#FAF6E9] dark:bg-[#1A1A1A] px-6 py-12 font-adlam">
      <div className="max-w-6xl mx-auto flex flex-col lg:flex-row items-start gap-12">
        <div className="w-full lg:w-1/3">
          <h2 className="text-xl font-bold text-[#1E6DB9] mb-4">Players:</h2>
          <div className="h-64 bg-[#E2E2E2] rounded-xl p-4 overflow-auto">
            {players.map((p, i) => (
              <div key={i} className="mb-2 text-[#1E6DB9]">
                 {p.name}
              </div>
            ))}
          </div>
        </div>

        <div className="w-full lg:w-1/3 flex flex-col gap-6">
          <div>
            <h3 className="text-lg font-bold text-[#1E6DB9] mb-4">URL:</h3>
            <div className="bg-[#E2E2E2] rounded-full px-6 py-2 text-[#1E6DB9] w-full max-w-xs">
              {gameUrl}
            </div>
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#1E6DB9] mb-2">Code:</h3>
            <div className="bg-[#E2E2E2] rounded-full px-8 py-4 inline-block text-[#1E6DB9]">
              {gameCode}
            </div>
          </div>
        </div>

        <div className="w-full lg:w-1/3">
          <h3 className="text-lg font-bold text-[#1E6DB9] mb-4">QR-code:</h3>
          <div className="bg-[#E2E2E2] p-4 rounded-xl inline-block">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(
                gameUrl
              )}`}
              alt="QR-code"
              className="rounded-lg"
            />
          </div>
        </div>
      </div>

      {isHost && (
        <div className="mt-12 text-center">
          <button
            onClick={handleStartGame}
            className="bg-[#1E6DB9] text-[#FAF6E9] px-8 py-3 rounded-full text-lg font-medium hover:opacity-90 transition"
          >
            Create teams
          </button>
        </div>
      )}
    </div>
  );
};


export default Lobby;
