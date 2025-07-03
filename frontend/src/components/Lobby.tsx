import React, { useEffect, useState, useRef } from 'react';
import * as config from './config';

function Lobby() {
  const args = useRef<config.Arguments>({ name: '', code: '', isHost: false });
  const [players, setPlayers] = useState<string[]>([]);
  const [socket, setSocket] = useState<WebSocket>();
  const { name, code, isHost } = args.current;
  const gameUrl = `http://${window.location.host}?code=${code}`;

  useEffect(() => {
    args.current = config.getArgs();
    if (!args.current.code || !args.current.name) return;

    let ws: WebSocket;
    if (args.current.isHost) {
      ws = config.connectSocketHost(args.current.name, args.current.code);
    } else {
      ws = config.connectSocketPlayer(args.current.name, args.current.code);
    }
    setSocket(ws);
    ws.onopen = () => {};
    ws.onmessage = (message) => {
      const data = JSON.parse(message.data);
      if (isHost) {
        let sup: string[] = [];
        Object.keys(data.teams)
          .forEach((teamId) => { sup = sup.concat(data.teams[teamId].players); });
        if (sup) {
          setPlayers(sup);
        }
      } else {
        setPlayers(Object.keys(data.team_scores));
      }
      if (data.game_state === 'in_progress') {
        config.setInitialState(data);
        config.navigateTo(config.Page.Quiz, args.current);
      }
    };
  }, [code, name, isHost]);

  const handleStartGame = () => {
    socket?.send(JSON.stringify({ action: 'start_game' }));
    config.navigateTo(config.Page.Quiz, args.current);
  };

  return (
    <div className="min-h-screen pt-32 px-9 bg-[#FAF6E9] dark:bg-[#1A1A1A] px-6 py-12 font-adlam">
      <div className="max-w-6xl mx-auto flex flex-col lg:flex-row items-start gap-12">
        <div className="w-full lg:w-1/3">
          <h2 className="text-xl font-bold text-[#1E6DB9] mb-4">Players:</h2>
          <div className="h-64 bg-[#E2E2E2] rounded-xl p-4 overflow-auto">
            {players.map((p) => (
              <div key={p} className="mb-2 text-[#1E6DB9]">
                {p}
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
              {code}
            </div>
          </div>
        </div>

        <div className="w-full lg:w-1/3">
          <h3 className="text-lg font-bold text-[#1E6DB9] mb-4">QR-code:</h3>
          <div className="bg-[#E2E2E2] p-4 rounded-xl inline-block">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(
                gameUrl,
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
            type="button"
            onClick={handleStartGame}
            className="bg-[#1E6DB9] text-[#FAF6E9] px-8 py-3 rounded-full text-lg font-medium hover:opacity-90 transition disabled:bg-gray-400"
            disabled={players.length === 0}
          >
            Start game
          </button>
        </div>
      )}
    </div>
  );
}

export default Lobby;
