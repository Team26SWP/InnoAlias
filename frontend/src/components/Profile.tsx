import React, { useEffect, useState } from 'react';
import * as config from './config';

function Profile() {
  const [profile, setProfile] = useState<config.UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [decks, setDecks] = useState<config.Deck[]>([
    {
      id: 'Aboba',
      name: 'Abobny',
      words_count: 10,
      tags: [],
    },
  ]);
  const [tags, setTags] = useState<string[]>([]);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [searchString, setSearchString] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${config.HTTP_URL}/profile/me`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          setError('Failed to fetch profile.');
          setLoading(false);
          return;
        }
        const data: config.UserProfile = await response.json();
        setProfile(data);
        config.setProfile(data);
        setDecks(data.decks);
        let supp: string[] = [];
        data.decks.forEach((deck) => {
          supp = supp.concat(deck.tags);
        });
        setTags(supp);
      } catch (err) {
        setError('An unexpected error occurred.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const selectTag = (event: React.MouseEvent) => {
    if (!(event.target instanceof HTMLButtonElement)) { return; }
    if (event.target.textContent === selectedTag) {
      setSelectedTag(null);
      return;
    }
    setSelectedTag(event.target.textContent);
  };

  const searchInput = (event: React.ChangeEvent) => {
    if (!(event.target instanceof HTMLInputElement)) { return; }
    setSearchString(event.target.value);
  };

  const selectDeck = async (event: React.MouseEvent) => {
    if (!(event.target instanceof HTMLButtonElement)) { return; }
    const deckId = event.target.id;
    const response = await fetch(`${config.HTTP_URL}/profile/deck/${deckId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    const data = await response.json();
    config.saveCreationState(config.loadCreationState().settings, config.loadCreationState().words
      .concat(data.words));
    config.setDeckChoice(false);
    config.navigateTo(config.Page.Create);
  };

  function checkDeck(deck: config.Deck) {
    return ((!selectedTag) || deck.tags.indexOf(selectedTag) !== -1)
      && ((!searchString) || deck.name.includes(searchString));
  }

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return (
      <div>
        Error:
        {error}
      </div>
    );
  }

  if (!profile) {
    return <div>No profile data available</div>;
  }

  return (
    <div className="min-h-screen bg-[#FAF6E9] px-6 py-10 font-adlam text-[#1E6DB9]">
      <div hidden={config.getDeckChoice()}>
        <h1 className="text-4xl font-bold mb-6">Profile</h1>
        <div className="flex items-center mb-10 gap-6">
          <div className="w-36 h-36 bg-gray-300 rounded-full" />
          <div>
            <h2 className="text-4xl font-bold">{profile.name}</h2>
            <p className="text-black text-7sm font-semibold">{profile.email}</p>
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <input
          onChange={searchInput}
          type="text"
          placeholder="Search desks or tags"
          className="w-full md:max-w-md p-3 rounded-full border border-gray-300 shadow-sm placeholder:text-[#1E6DB9] text-[#1E6DB9] font-semibold"
        />

        <div className=" overflow-x-scroll whitespace-nowrap mt-3 md:mt-0">
          <div className="flex gap-2">
            {tags.map((tag) => (
              <button
                type="button"
                key={tag}
                className="bg-[#e0e0e0] hover:bg-[#d5d5d5] text-[#1E6DB9] px-4 py-1 rounded-md text-sm font-bold transition whitespace-nowrap"
                onClick={selectTag}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 md:grid-cols-3 gap-4 mt-8">
        {decks.filter((deck) => checkDeck(deck)).map((deck) => (
          <button
            onClick={selectDeck}
            type="button"
            key={deck.id}
            id={deck.id}
            className="bg-[#d9d9d9] hover:bg-[#c9c9c9] text-[#1E6DB9] font-bold text-sm py-5 px-4 rounded-lg shadow-sm transition"
          >
            {deck.name}
          </button>
        ))}
      </div>
    </div>
  );
}

export default Profile;
