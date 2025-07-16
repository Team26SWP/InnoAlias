import React, { useEffect, useState } from 'react';
import * as config from './config';
import AdminPanelMenu from './AdminPanelMenu';

type DeckWithWords = config.Deck & { words: string[], private: boolean };

function Profile() {
  const [profile, setProfile] = useState<config.UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [decks, setDecks] = useState<config.Deck[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [searchString, setSearchString] = useState<string | null>(null);
  const [deckLoad, setDeckLoad] = useState<boolean>(false);
  const [deckCreate, setDeckCreate] = useState<boolean>(false);

  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [isEditingAll, setIsEditingAll] = useState<boolean>(false);
  const [draft, setDraft] = useState<DeckWithWords | null>(null);
  const [newWordText, setNewWordText] = useState<string>('');

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
        if (response.status === 401) {
          const refresh = await fetch(`${config.HTTP_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: localStorage.getItem('refresh_token') }),
          });
          const newToken = await refresh.json();
          if (refresh.ok) {
            localStorage.setItem('access_token', newToken.access_token);
            localStorage.setItem('refresh_token', newToken.refresh_token);
            await fetchProfile();
            return;
          }
        }
        setError('Failed to fetch profile.');
        setLoading(false);
        return;
      }
      const data: config.UserProfile = await response.json();
      setProfile(data);
      config.setProfile(data);
      setDecks(data.decks);
      const supp: string[] = [];
      data.decks.forEach((deck) => {
        deck.tags.forEach((tag) => {
          if (!supp.includes(tag)) {
            supp.push(tag);
          }
        });
      });
      setTags(supp);
    } catch (err) {
      setError('An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    setDeckLoad(config.getDeckChoice());
  }, []);

  const selectTag = (event: React.MouseEvent) => {
    const btn = event.target;
    if (!(btn instanceof HTMLButtonElement)) { return; }
    if (!(btn.textContent)) { return; }
    if (selectedTags.includes(btn.textContent)) {
      setSelectedTags(selectedTags.filter((tag) => (tag !== btn.textContent)));
      return;
    }
    setSelectedTags(selectedTags.concat(btn.textContent));
  };

  const searchInput = (event: React.ChangeEvent) => {
    if (!(event.target instanceof HTMLInputElement)) { return; }
    setSearchString(event.target.value);
  };

  const openModal = async (index: number) => {
    if (index === -1) {
      setDeckCreate(true);
      setDraft({
        id: '',
        name: '',
        words_count: 0,
        tags: [],
        words: [],
        private: true,
      });
      setIsEditingAll(true);
    } else {
      const deckId = decks[index].id;

      const response = await fetch(`${config.HTTP_URL}/profile/deck/${deckId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();
      setDraft({ ...decks[index], words: data.words, private: data.private });
      setIsEditingAll(false);
    }
    setActiveIndex(index);
    setNewWordText('');
  };

  const closeModal = () => {
    setActiveIndex(null);
    setIsEditingAll(false);
    setNewWordText('');
  };

  const toggleEditAll = () => {
    if (activeIndex !== null && !isEditingAll) {
      setDraft({ ...draft!, words: draft!.words });
    }
    setIsEditingAll((prev) => !prev);
  };

  const deleteDeck = async () => {
    if (activeIndex === null) return;
    const deckId = decks[activeIndex].id;
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(`${config.HTTP_URL}/profile/deck/${deckId}/delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        setError('Failed to delete deck.');
        return;
      }
      setDecks((prev) => prev.filter((_, idx) => idx !== activeIndex));
      closeModal();
    } catch (err) {
      setError('An unexpected error occurred while deleting the deck.');
    }
  };

  const updateDraftWord = (idx: number, text: string) => {
    if (!draft) return;
    const newWords = [...draft.words];
    newWords[idx] = text;
    setDraft({ ...draft, words: newWords });
  };

  const deleteDraftWord = (idx: number) => {
    if (!draft) return;
    setDraft({ ...draft, words: draft.words.filter((_, i) => i !== idx) });
  };

  const addDraftWord = () => {
    if (!draft || newWordText.trim() === '' || draft.words.includes(newWordText.trim())) return;
    setDraft({ ...draft, words: [...draft.words, newWordText.trim()] });
    setNewWordText('');
  };

  const saveAll = async () => {
    if (activeIndex === null || !draft) return;
    const deckId = decks[activeIndex].id;
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(`${config.HTTP_URL}/profile/deck/${deckId}/edit`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          deck_name: draft.name,
          words: draft.words,
          tags: draft.tags || [],
        }),
      });
      if (!response.ok) {
        setError('Failed to update deck.');
        return;
      }
      const updatedDeck = await response.json();
      setDecks((prev) => prev.map((deck, idx) => {
        if (idx === activeIndex) {
          return {
            ...deck,
            ...updatedDeck,
            words_count: updatedDeck.words.length,
          };
        }
        return deck;
      }));
      setIsEditingAll(false);
    } catch (err) {
      setError('An unexpected error occurred while updating the deck.');
    }
  };

  const cancelAll = () => {
    if (activeIndex !== null && draft) setDraft({ ...draft });
    setIsEditingAll(false);
    setNewWordText('');
  };

  function checkDeck(deck: config.Deck) {
    for (let i = 0; i < selectedTags.length; i += 1) {
      if (!deck.tags.includes(selectedTags[i])) { return false; }
    }
    if (!searchString) { return true; }
    return deck.name.toLowerCase().includes(searchString.toLowerCase());
  }

  function toPage(page : 'Home' | 'Create' | 'Join' | 'Ai') {
    if (page === 'Home') { config.navigateTo(config.Page.Home); }
    if (page === 'Create') { config.navigateTo(config.Page.Create); }
    if (page === 'Join') { config.navigateTo(config.Page.Join); }
    if (page === 'Ai') { config.navigateTo(config.Page.AiCreate); }
  }

  const selectDeck = async () => {
    if (!draft || !draft.words) { return; }
    config.addWords(draft.words);
    if (config.loadCreationState().aiGame) {
      toPage('Ai');
      return;
    }
    toPage('Create');
  };

  const createDeck = async () => {
    if (!draft) { return; }
    await fetch(`${config.HTTP_URL}/profile/deck/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({
        deck_name: draft.name,
        words: draft.words,
        tags: draft.tags,
        private: draft.private,
      }),
    });
    setIsEditingAll(false);
    setDraft(null);
    fetchProfile();
  };

  function logOut() {
    localStorage.removeItem('access_token');
    config.setProfile(null);
    toPage('Home');
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
    <div className="min-h-screen bg-[#FAF6E9] dark:bg-[#1A1A1A] px-10 py-0.5 font-adlam text-[#1E6DB9]">
      {profile.isAdmin && <AdminPanelMenu />}
      {!deckLoad && (
        <>
          <div className="flex justify-between items-center mb-6 mt-5">
            <button type="button" className="py-1 text-xl left-4 text-[#1E6DB9] hover:underline" onClick={() => config.navigateTo(config.Page.Home)}>←Back to main</button>
            <button type="button" onClick={logOut} className="px-4 py-2 bg-[#1E6DB9] text-white rounded-md hover:bg-gray-300 transition">Sign out</button>
          </div>
          <h1 className="py-1 text-2xl sm:text-3xl md:text-3xl mb-6 font-bold ">Profile</h1>
          <div className="flex items-center mb-10 gap-5">
            <div className="w-36 h-36 bg-[#c9c9c9] rounded-full" />
            <div>
              <h2 className="text-4xl font-bold">
                {profile.name}
                &nbsp;
                {profile.surname}
              </h2>
              <p className="text-black dark:text-white text-7sm font-semibold">{profile.email}</p>
            </div>
          </div>
        </>
      )}

      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        {deckLoad && (<button type="button" onClick={() => { if (config.loadCreationState().aiGame) { toPage('Ai'); return; } toPage('Create'); }} className="px-4 py-2 bg-[#1E6DB9] text-white rounded-md hover:bg-gray-300 transition">Cancel deck load</button>)}
        <input
          onChange={searchInput}
          type="text"
          placeholder="Search decks"
          className="w-full md:max-w-md p-3 rounded-full bg-[#c9c9c9] shadow-sm placeholder:text-[#1E6DB9] text-[#1E6DB9] dark:text-white font-semibold"
        />
      </div>
      <div> </div>
      <div className="overflow-x-scroll whitespace-nowrap mt-4 hide-scrollbar">
        <div className="flex gap-2">
          {tags.map((tag) => (
            <button
              type="button"
              key={tag}
              className={`px-4 py-1 rounded-md text-sm font-bold transition whitespace-nowrap ${selectedTags.includes(tag) ? 'bg-[#1E6DB9] text-white' : 'bg-[#e0e0e0] text-[#1E6DB9] hover:bg-[#d5d5d5]'}`}
              onClick={selectTag}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 md:grid-cols-3 gap-4 mt-8">
        <div
          role="button"
          tabIndex={0}
          onClick={() => openModal(-1)}
          onKeyDown={(e) => e.key === 'Enter' && openModal(-1)}
          className="cursor-pointer bg-[#d9d9d9] hover:bg-[#c9c9c9] text-[#1E6DB9] font-bold text-sm py-5 px-4 rounded-lg shadow-sm transition"
        >
          <div>Create a deck</div>
        </div>
        {decks.filter((deck) => checkDeck(deck)).map((deck, idx) => (
          <div
            key={deck.id}
            role="button"
            tabIndex={0}
            onClick={() => openModal(idx)}
            onKeyDown={(e) => e.key === 'Enter' && openModal(idx)}
            className="cursor-pointer bg-[#d9d9d9] hover:bg-[#c9c9c9] text-[#1E6DB9] font-bold text-sm py-5 px-4 rounded-lg shadow-sm transition"
          >
            <div>{deck.name}</div>
            <div className="text-xs font-medium">
              {deck.words_count}
              {' '}
              words
            </div>
          </div>
        ))}
      </div>

      {activeIndex !== null && draft && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white p-6 rounded-lg w-96 max-w-md max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-7">
              <h3 className="text-2xl font-bold">
                {isEditingAll ? (
                  <input
                    value={draft.name}
                    onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                    className="border p-1 rounded w-48"
                  />
                ) : (
                  draft.name
                )}
              </h3>
              <div className="flex space-x-2">
                {isEditingAll ? (
                  <>
                    <button type="button" onClick={deckCreate ? createDeck : saveAll} className="px-2 py-1 text-[#1E6DB9] rounded text-sm">{deckCreate ? 'Create' : 'Save'}</button>
                    <button type="button" onClick={cancelAll} className="px-2 py-1 text-gray-500 rounded text-sm">Cancel</button>
                  </>
                ) : (
                  <>
                    <button type="button" onClick={toggleEditAll} className="px-2 py-1 bg-[#1E6DB9] text-white rounded text-sm">Edit</button>
                    <button type="button" onClick={deleteDeck} className="px-2 py-1 text-red-500 rounded text-sm">Delete</button>
                  </>
                )}
                <button type="button" onClick={closeModal} className="px-2 py-1 text-gray-500 hover:text-gray-700 text-sm">✕</button>
              </div>
            </div>

            {isEditingAll && (
              <>
                <label htmlFor="public" className="mr-10">
                  <input type="radio" id="public" name="isPublic" className="mr-2" defaultChecked onClick={() => { draft.private = false; }} />
                  Public
                </label>
                <label htmlFor="private" className="mr-10">
                  <input type="radio" id="private" name="isPublic" className="mr-2" onClick={() => { draft.private = true; }} />
                  Private
                </label>
                <div className="flex gap-2 mb-4">
                  <input
                    type="text"
                    placeholder="New word"
                    value={newWordText}
                    onChange={(e) => setNewWordText(e.target.value)}
                    className="flex-1 p-2 border rounded"
                  />
                  <button type="button" onClick={addDraftWord} className="px-4 py-2 bg-[#1E6DB9] text-white rounded hover:bg-[#185a9e] transition">Add</button>
                </div>
              </>
            )}

            <ul className="space-y-2">
              {draft.words.map((word, idx) => (
                <li key={word} className="flex justify-between items-center">
                  {isEditingAll ? (
                    <input
                      value={word}
                      onChange={(e) => updateDraftWord(idx, e.target.value)}
                      className="flex-1 p-2 border rounded"
                    />
                  ) : (
                    <span>{word}</span>
                  )}
                  {isEditingAll && (
                    <button type="button" onClick={() => deleteDraftWord(idx)} className="ml-2 text-gray-500 text-xs">Delete</button>
                  )}
                </li>
              ))}
            </ul>
            <div className="flex space-x-2 items-center justify-end mt-7">
              {!isEditingAll && (<button type="button" onClick={selectDeck} className="px-2 py-1 bg-[#1E6DB9] text-white rounded text-sm">Use</button>)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Profile;
