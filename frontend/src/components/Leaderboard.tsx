import React, { useEffect, useState } from 'react';
import * as config from './config';

const { HTTP_URL } = config;

interface TeamScore {
  players: { [name: string]: number },
  total_score: number;
}

export function Leaderboard() {
  const [teams, setTeams] = useState<{ [teamName: string]: TeamScore }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const { code } = config.getArgs();
    const fetchLeaderboard = async () => {
      try {
        const response = await fetch(
          `${HTTP_URL}/game/leaderboard/${code}`,
        );
        if (!response.ok) {
          if (response.status === 404) {
            setError('Game not found.');
          } else {
            setError('Failed to fetch leaderboard.');
          }
          throw new Error('Failed to fetch leaderboard');
        }

        const ts: { [teamName: string]: TeamScore } = await response.json();
        setTeams(ts);
      } catch (err) {
        setError('An error occurred while fetching the leaderboard.');
      } finally {
        setLoading(false);
      }
    };

    if (code) {
      fetchLeaderboard();
    }
  }, []);

  const saveDeck = async () => {
    const { code } = config.getArgs();
    const response = await fetch(`${HTTP_URL}/game/${code}/deck`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await response.json();
    const deckName = prompt('Please, input the name of the deck');
    if (!deckName) { return; }
    const tags = prompt('Please, input tags separated by commas')?.split(',');
    await fetch(`${HTTP_URL}/game/deck/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({
        deck_name: deckName,
        tags: tags || [],
        words: data.words,
      }),
    });
  };

  const exportDeck = async () => {
    const name = prompt('Input the name of the file');
    if (!name) { return; }
    const response = await fetch(`${HTTP_URL}/game/leaderboard/${config.getArgs().code}/export`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/txt',
      },
    });
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);

    const link: HTMLAnchorElement = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute(
      'download',
      `${name}.txt`,
    );
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
  };

  const toMain = () => {
    config.navigateTo(config.Page.Home);
  };

  if (loading) {
    return <div className="leaderboard-container">Loading...</div>;
  }

  if (error) {
    return (
      <div className="leaderboard-container">
        Error:
        {error}
      </div>
    );
  }

  return (
    <div className="bg-[#FAF6E9] dark:bg-[#1A1A1A] min-h-screen px-4 py-10 min-h-screen flex flex-col items-center font-[ADLaM_Display]">
      <h1 className="text-3xl font-bold text-[#3171a6] mb-6">Leaderboard</h1>

      <div className="bg-[#d9d9d9] rounded-xl w-full max-w-3xl p-4 max-h-[400px] overflow-y-auto flex flex-col gap-2 mb-8">
        {Object.keys(teams).map((team, index) => (
          <div key={team}>
            <div
              key={team}
              className="bg-[#bfbfbf] rounded-lg px-4 py-2 flex justify-between items-center text-[#3171a6] font-bold text-lg"
            >
              <span>
                {index + 1}
              </span>
              <span>{team}</span>
              <span>{teams[team].total_score}</span>
            </div>
            {Object.keys(teams[team].players).map((player, indexP) => (
              <div
                key={player}
                className="bg-[#bfbfbf] rounded-lg px-4 py-2 ml-10 mt-2 flex justify-between items-center text-[#3171a6] font-bold text-lg"
              >
                <span>
                  {index + 1}
                  .
                  {indexP + 1}
                </span>
                <span>{player}</span>
                <span>{teams[team].players[player]}</span>
              </div>
            ))}
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap justify-center gap-4">
        <button type="button" className="bg-[#d9d9d9] text-[#3171a6] text-xl px-5 py-2 rounded-lg font-semibold" onClick={exportDeck}>
          Export Deck
        </button>
        <button
          type="button"
          onClick={toMain}
          className="bg-[#3171a6] text-[#fff1e8] text-xl px-5 py-2 rounded-lg font-semibold"
        >
          Back to main
        </button>
        <button
          type="button"
          onClick={saveDeck}
          className="bg-[#d9d9d9] text-[#3171a6] text-xl px-5 py-2 rounded-lg font-semibold"
        >
          Save Deck
        </button>
      </div>
    </div>
  );
}
// <button className="button light">Export Leaderboard</button>

export default Leaderboard;
