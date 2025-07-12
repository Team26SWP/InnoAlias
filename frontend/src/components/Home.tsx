import React, {
  useState, useEffect, useMemo, useCallback,
} from 'react';
import * as config from './config';

interface Deck {
  id: string
  name: string
  termCount: number
  ownerName: string
  terms: string[]
  tags: string[]
}

interface CreateParams {
  deckId: string
}

interface GalleryResponse {
  decks: Deck[]
  total_count: number
}

async function fetchGallery(page: number = 1): Promise<GalleryResponse> {
  const response = await fetch(`${config.HTTP_URL}/gallery/decks?number=${page}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error('Failed to load gallery');
  }
  return response.json();
}

async function saveDeck(deckId: string): Promise<string> {
  const response = await fetch(`${config.HTTP_URL}/gallery/decks/${deckId}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error('Failed to save deck');
  }
  const result = await response.json();
  return result.id;
}

function Home() {
  const [apiGallery, setApiGallery] = useState<Deck[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [visibleCount, setVisibleCount] = useState<number>(8);
  const [showGallery, setShowGallery] = useState<boolean>(false);
  const [selectedDeck, setSelectedDeck] = useState<Deck | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [saveLoading, setSaveLoading] = useState<boolean>(false);

  const isLoggedIn = Boolean(localStorage.getItem('access_token'));

  const handleScroll = useCallback((): void => {
    setShowGallery(window.scrollY > 0);
  }, []);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);

  const loadGallery = useCallback(async (page: number = 1): Promise<void> => {
    try {
      setIsLoading(true);
      const data = await fetchGallery(page);
      const decks = data.decks as Deck[];
      setApiGallery([...decks].reverse());
      setTotalCount(data.total_count);
    } catch (error) {
      console.error('Failed to load gallery:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadMoreGallery = useCallback(async (): Promise<void> => {
    try {
      const nextPage = currentPage + 1;
      const data = await fetchGallery(nextPage);
      const decks = data.decks as Deck[];
      setApiGallery((prev) => [...prev, ...decks]);
      setCurrentPage(nextPage);
    } catch (error) {
      console.error('Failed to load more gallery:', error);
    }
  }, [currentPage]);
  const loadProfile = async () => {
    const response = await fetch(`${config.HTTP_URL}/profile/me`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    });
    const profile = await response.json();
    if (response.ok) {
      config.setProfile(profile);
    }
  };
  const handleSaveDeck = useCallback(async (deckId: string): Promise<void> => {
    if (!isLoggedIn) {
      config.navigateTo(config.Page.Login);
      return;
    }
    try {
      setSaveLoading(true);
      await saveDeck(deckId);
      const profile = config.getProfile();
      if (profile) {
        await loadProfile();
      }
    } catch (error) {
      console.error('Failed to save deck:', error);
    } finally {
      setSaveLoading(false);
    }
  }, [isLoggedIn]);

  useEffect(() => {
    loadGallery();
    config.closeConnection();
    config.resetGameCreation();
    async function gameLoad() {
      if (!config.getProfile() && localStorage.getItem('access_token')) {
        await loadProfile();
      }
      const code = new URLSearchParams(window.location.search).get('code');
      const profile = config.getProfile();
      if (!profile && code) {
        config.navigateTo(config.Page.Login);
      }
      if (profile && code) {
        config.navigateTo(config.Page.Join, { name: profile.name, code, isHost: false });
      }
    }
    gameLoad();
  }, [loadGallery]);

  const filtered = useMemo<Deck[]>(() => {
    const term = searchTerm.trim().toLowerCase();
    return apiGallery.filter((t) => {
      const inName = t.name.toLowerCase().includes(term);
      const inTags = t.tags.some((tag) => tag.toLowerCase().includes(term));
      return inName || inTags;
    });
  }, [apiGallery, searchTerm]);

  const handleCreateGame = useCallback((): void => {
    config.navigateTo(isLoggedIn ? config.Page.Create : config.Page.Login);
  }, [isLoggedIn]);

  const handleCreateAiGame = useCallback((): void => {
    config.navigateTo(isLoggedIn ? config.Page.AiCreate : config.Page.Login);
  }, [isLoggedIn]);

  const handleJoinGame = useCallback((): void => {
    config.navigateTo(isLoggedIn ? config.Page.Join : config.Page.Login);
  }, [isLoggedIn]);

  const handleProfile = useCallback((): void => {
    config.navigateTo(config.Page.Profile);
  }, []);

  const handleLogin = useCallback((): void => {
    config.navigateTo(config.Page.Login);
  }, []);

  const useThisDeck = useCallback((): void => {
    if (!selectedDeck) return;
    // @ts-expect-error extra args
    config.navigateTo(config.Page.Create, { deckId: selectedDeck.id } as CreateParams);
    // нужно правильно настроить
  }, [selectedDeck]);

  return (
    <div className="bg-[#FAF6E9] dark:bg-[#1A1A1A] text-[#1E6DB9]">
      <div className="relative h-screen flex flex-col items-center justify-center px-6">
        <button
          type="button"
          aria-label={isLoggedIn ? 'Profile' : 'Log in'}
          onClick={isLoggedIn ? handleProfile : handleLogin}
          className="absolute top-4 right-4 bg-[#1E6DB9] text-[#FAF6DB] font-semibold px-4 py-2 rounded-full hover:opacity-90 transition"
        >
          {isLoggedIn ? 'Profile' : 'Log in'}
        </button>
        <h1 className="text-9xl font-bold font-adlam mb-8">alias</h1>
        <div className="flex gap-4">
          <button
            type="button"
            onClick={handleCreateGame}
            className="bg-[#1E6DB9] text-[#FAF6DB] font-adlam px-6 py-3 rounded-lg text-lg font-medium hover:opacity-90 transition"
          >
            Create lobby
          </button>
          <button
            type="button"
            onClick={handleJoinGame}
            className="border border-[#1E6DB9] bg-transparent text-[#1E6DB9] font-adlam px-6 py-3 rounded-lg text-lg font-medium hover:opacity-90 transition"
          >
            Join game
          </button>
          <button
            type="button"
            onClick={handleCreateAiGame}
            className="bg-[#1E6DB9] text-[#FAF6DB] font-adlam px-6 py-3 rounded-lg text-lg font-medium hover:opacity-90 transition"
          >
            Singleplayer
          </button>
        </div>
      </div>
      <div
        className={`w-full max-w-5xl mx-auto px-6 pb-10 transition-opacity duration-500 ${
          showGallery ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        aria-hidden={showGallery}
      >

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-4xl font-semibold">Gallery:</h2>
          <input
            type="text"
            placeholder="Search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-4 py-2 border rounded-full text-sm focus:outline-none focus:ring w-full sm:w-1/2 lg:w-1/3"
          />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
          {filtered.slice(0, visibleCount).map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setSelectedDeck(item)}
              className="bg-gray-300 p-4 rounded-lg hover:opacity-90 transition text-left"
            >
              <h3 className="font-semibold mb-1">{item.name}</h3>
              <p className="text-xs text-gray-400">
                {item.termCount}
                {' '}
                terms
              </p>
              <p className="text-xs text-gray-400">{item.ownerName}</p>
            </button>
          ))}
        </div>
        {visibleCount < filtered.length && (
        <button
          type="button"
          onClick={() => setVisibleCount((c) => c + 8)}
          className="mt-6 block mx-auto hover:underline font-adlam"
        >
          Show more
        </button>
        )}
        {apiGallery.length > 0 && visibleCount >= filtered.length && currentPage * 50 < totalCount && (
        <button
          type="button"
          onClick={loadMoreGallery}
          disabled={isLoading}
        >
          {isLoading ? 'Loading...' : 'Load more'}
        </button>
        )}
      </div>
      {selectedDeck && (
        <>
          <button
            type="button"
            aria-label="Close modal"
            className="fixed inset-0 z-60 bg-black bg-opacity-50 hover:bg-opacity-50 focus:bg-opacity-50 active:bg-opacity-50 focus:outline-none"
            onClick={() => setSelectedDeck(null)}
          />
          <div
            className="fixed inset-0 z-70 bg-black bg-opacity-50 flex items-center justify-center p-4 pointer-events-auto"
            role="dialog"
            aria-modal="true"
          >
            <div className="bg-gray-300 rounded-lg max-w-md w-full p-6 space-y-4 z-60" onClick={(e) => e.stopPropagation()}>
              <h3 className="text-3xl font-bold">{selectedDeck.name}</h3>
              <ul className="max-h-48 overflow-y-auto list-disc list-inside space-y-1">
                {selectedDeck.terms.map((term) => (
                  <li key={`${selectedDeck.id}-${term}`} className="text-xl">
                    {term}
                  </li>
                ))}
              </ul>
              <div className="flex justify-end gap-3 mt-4">
                <button
                  type="button"
                  onClick={() => setSelectedDeck(null)}
                  className="px-4 py-2 font-semibold text-[#FAF6E9]"
                >
                  Cancel
                </button>
                {isLoggedIn && (
                  <button
                    type="button"
                    onClick={() => handleSaveDeck(selectedDeck.id)}
                    disabled={saveLoading}
                  >
                    {saveLoading ? 'Saving...' : 'Save to profile'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={useThisDeck}
                  className="px-4 py-2 bg-[#3171a6] text-[#FAF6E9] rounded hover:opacity-90 transition"
                >
                  Use this deck
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Home;
