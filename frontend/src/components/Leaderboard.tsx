import React, { useEffect, useRef, useState } from 'react';
import * as config from './config';

const { HTTP_URL } = config;

interface TeamScore {
  players: { [name: string]: number };
  total_score: number;
}

export function Leaderboard() {
  const [teams, setTeams] = useState<{ [teamName: string]: TeamScore }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deckName, setDeckName] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const isPrivate = useRef(false);
  const [allTags, setAllTags] = useState<string[]>([]);

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

    if (config.getArgs().code) {
      fetchLeaderboard();
    }
  }, []);

  useEffect(() => {
    if (!isModalOpen) { return; }
    const profile = config.getProfile();
    if (!profile) { return; }
    let supp: string[] = [];
    profile.decks.forEach((deck) => {
      supp = supp.concat(deck.tags.filter((tag) => !supp.includes(tag)));
    });
    setAllTags(supp);
  }, [isModalOpen]);

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => {
    setIsModalOpen(false);
    setDeckName('');
    setTagInput('');
    setTags([]);
    setAllTags([]);
  };

  const addTag = (tag?: string) => {
    const newTag = tag?.trim() ?? tagInput.trim();
    if (newTag && !tags.includes(newTag)) {
      setTags([...tags, newTag]);
    }
    setTagInput('');
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const saveDeck = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('You must be logged in to save a deck.');
      return;
    }
    const profile = config.getProfile();
    if (!profile) { return; }
    if (profile.decks.map((deck) => deck.name.toLowerCase()).includes(deckName.toLowerCase())) {
      alert('Deck with this name already exists');
      return;
    }
    let words: string[] = [];
    try {
      const deckResp = await fetch(`${HTTP_URL}/game/deck/${config.getArgs().code}`);
      if (!deckResp.ok) {
        alert('Failed to fetch deck words for this game.');
        return;
      }
      const deckData = await deckResp.json();
      words = deckData.words || [];
    } catch (err) {
      alert('An error occurred while fetching the deck words.');
      return;
    }
    try {
      const saveResp = await fetch(`${HTTP_URL}/profile/deck/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          deck_name: deckName,
          words,
          tags,
          isPrivate,
        }),
      });
      if (saveResp.ok) {
        closeModal();
      } else if (saveResp.status === 404) {
        alert('User record not found.');
      } else if (saveResp.status === 401) {
        alert('Unauthorized. Please log in again.');
      } else {
        alert('Failed to save deck.');
      }
    } catch (err) {
      alert('An error occurred while saving the deck.');
    }
  };

  const exportDeck = async () => {
    const name = prompt('Input the name of the file');
    const profile = config.getProfile();
    if (!deckName || !profile) { return; }

    const response = await fetch(`${HTTP_URL}/game/leaderboard/${config.getArgs().code}/export`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/txt',
      },
    });
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);

    const link = document.createElement('a');
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

  const filteredSuggestions = allTags
    .filter((t) => t.toLowerCase().startsWith(tagInput.trim().toLowerCase()))
    .filter((t) => !tags.includes(t));

  return (
    <div className="bg-[#FAF6E9] dark:bg-[#1A1A1A] min-h-screen px-4 py-10 flex flex-col items-center font-[ADLaM_Display]">
      <h1 className="text-3xl font-bold text-[#3171a6] mb-6">Leaderboard</h1>

      <div className="bg-[#d9d9d9] rounded-xl w-full max-w-3xl p-4 max-h-[400px] overflow-y-auto flex flex-col gap-2 mb-8">
        {Object.keys(teams).map((team, index) => (
          <div key={team}>
            {Object.keys(teams).length !== 1 && (
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
            )}
            {Object.keys(teams[team].players).map((player, indexP) => (
              <div
                key={player}
                className={`bg-[#bfbfbf] rounded-lg px-4 py-2 ${Object.keys(teams).length !== 1 && 'ml-10'} mt-2 flex justify-between items-center text-[#3171a6] font-bold text-lg`}
              >
                <span>
                  {Object.keys(teams).length !== 1 && `${index + 1}.`}
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
          onClick={openModal}
          className="bg-[#d9d9d9] text-[#3171a6] text-xl px-5 py-2 rounded-lg font-semibold"
        >
          Save Deck
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-[#DBD9D1] rounded-xl p-6 w-full max-w-md relative">
            <h2 className="text-2xl font-bold mb-4 text-[#3171a6]">Save Deck</h2>
            <div className="mb-4">
              <label htmlFor="deckName" className="block text-sm text-[#3171a6] font-medium mb-1">
                <span className="font-bold w-36">Deck Name</span>
                <div className="flex gap-2">
                  <input
                    id="deckName"
                    type="text"
                    value={deckName}
                    onChange={(e) => setDeckName(e.target.value)}
                    className="flex-1 border rounded px-3 py-2"
                    placeholder="Enter deck name"
                  />
                </div>
              </label>
            </div>
            <label htmlFor="public" className="mr-10">
              <input type="radio" id="public" name="isPublic" className="mr-2" defaultChecked onClick={() => { isPrivate.current = false; }} />
              Public
            </label>
            <label htmlFor="private" className="mr-10">
              <input type="radio" id="private" name="isPublic" className="mr-2" onClick={() => { isPrivate.current = true; }} />
              Private
            </label>
            <div className="mb-4 relative">
              <label htmlFor="tagInput" className="block text-sm text-[#3171a6] font-medium mb-1">
                <span className="font-bold w-36 inline-block">Tags</span>
                <div className="flex gap-2">
                  <input
                    id="tagInput"
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addTag()}
                    className="flex-1 border rounded px-3 py-2"
                    placeholder="Add a tag and press Enter"
                    list="tag-suggestions"
                    disabled={tags.length >= 5}
                  />
                  <button type="button" onClick={() => addTag()} className="px-4 py-2 bg-[#3171a6] text-white rounded">
                    Add
                  </button>
                </div>

                {filteredSuggestions.length > 0 && (
                <datalist id="tag-suggestions" className="absolute z-10 bg-white border rounded mt-1 w-full max-h-40 overflow-y-auto">
                  {filteredSuggestions.map((sug) => (
                    <option key={sug} value={sug}>
                      {sug}
                    </option>
                  ))}
                </datalist>
                )}
              </label>

              <div className="mt-2 flex flex-wrap gap-2">
                {tags.map((t) => (
                  <span key={t} className="flex items-center bg-[#d9d9d9] text-[#3171a6] px-3 py-1 rounded-full text-sm">
                    {t}
                    <button type="button" onClick={() => removeTag(t)} className="ml-2 font-bold">
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-4">
              <button type="button" onClick={closeModal} className="px-4 py-2 font-semibold">Cancel</button>
              <button type="button" onClick={saveDeck} className="px-4 py-2 bg-[#3171a6] text-[#FAF6E9] rounded font-semibold">Save Deck</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Leaderboard;
