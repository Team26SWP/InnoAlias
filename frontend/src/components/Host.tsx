import { useState, useEffect, useRef } from 'react';
import * as config from './config';

function Host() {
  const [teams, setTeams] = useState<{ [id: string]: config.TeamGameState }>({});
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const initialState = config.getInitialHostState();
    if (!initialState) { return; }
    setTeams(initialState.teams);
    ws.current = config.connectSocketHost(config.getArgs().name, config.getArgs().code);
    ws.current.onmessage = async (event) => {
      const data: config.HostGameState = await JSON.parse(event.data);
      setTeams(data.teams);

      if (data.game_state === 'finished') {
        config.navigateTo(config.Page.Leaderboard, config.getArgs());
      }
    };
  }, []);

  function endGame() {
    ws.current?.send(JSON.stringify({ action: 'stop_game' }));
  }

  function summ(arr: number[]) {
    let n = 0;
    for (let i = 0; i < arr.length; i += 1) {
      n += arr[i];
    }
    return n;
  }

  return (
    <div className="bg-[#FAF6E9] dark:bg-[#1A1A1A] min-h-screen px-4 py-10 min-h-screen flex flex-col items-center font-[ADLaM_Display]">
      <h1 className="text-3xl font-bold text-[#3171a6] mb-6">Game in progress</h1>

      <div className="bg-[#d9d9d9] rounded-xl w-full max-w-3xl p-4 max-h-[400px] overflow-y-auto flex flex-col gap-2 mb-8">
        {Object.keys(teams).length > 0 ? (Object.keys(teams).map((id, index) => (
          <div
            key={id}
            className="bg-[#bfbfbf] rounded-lg px-4 py-2 flex justify-between items-center text-[#3171a6] font-bold text-lg"
          >
            <span>
              {index + 1}
              .
            </span>
            <span>{teams[id].name}</span>
            <span>{summ((Object.values(teams[id].scores)))}</span>
          </div>
        ))) : 'No team has scored yet!'}
      </div>

      <div className="mt-6 flex flex-wrap justify-center gap-4">
        <button
          type="button"
          onClick={endGame}
          className="bg-[#3171a6] text-[#fff1e8] text-xl px-5 py-2 rounded-lg font-semibold"
        >
          End Game
        </button>
      </div>
    </div>
  );
}

export default Host;
