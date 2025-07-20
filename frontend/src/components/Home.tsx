import React, {
  useState, useEffect, useMemo, useCallback,
} from 'react';
import * as config from './config';

interface Deck {
  _id: string
  name: string
  words: string[]
  tags: string[]
  ownerids?: string[]
  private?: boolean
}

interface GalleryResponse {
  gallery: Deck[]
  total_decks: number
}

async function fetchGallery(page: number = 1): Promise<GalleryResponse> {
  const response = await fetch(`${config.HTTP_URL}/gallery/decks?page=${page}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error('Failed to load gallery');
  }
  return response.json();
}

function Home() {
  const [profile, setProfile] = useState<config.UserProfile | null>(null);
  const [apiGallery, setApiGallery] = useState<Deck[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [showGallery, setShowGallery] = useState<boolean>(false);
  const [selectedDeck, setSelectedDeck] = useState<Deck | null>(null);
  const [saveLoading, setSaveLoading] = useState<boolean>(false);

  const [isLoggedIn, setIsLoggedIn] = useState(Boolean(localStorage.getItem('access_token')));

  const handleScroll = useCallback((): void => {
    setShowGallery(window.scrollY > 0);
  }, []);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);

  const loadProfile = async () => {
    const valid = await config.validateToken();
    if (!valid) {
      setIsLoggedIn(false);
      return;
    }
    const response = await fetch(`${config.HTTP_URL}/profile/me`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    });
    const newProfile = await response.json();
    setProfile(newProfile);
    config.setProfile(newProfile);
  };

  const loadGallery = useCallback(async (pageToLoad: number = 1, append = false): Promise<void> => {
    try {
      setLoadingMore(true);
      const data = await fetchGallery(pageToLoad);
      const decks = data.gallery as Deck[];
      setHasMore((decks.length > 0) && ((apiGallery.length + decks.length) < data.total_decks));
      setApiGallery((prev) => (append ? [...prev, ...decks] : decks));
    } catch (error) {
      setHasMore(false);
      console.error('Failed to load gallery:', error);
    } finally {
      setLoadingMore(false);
    }
  }, [searchTerm, apiGallery.length]);

  // Инфинити скрол
  useEffect(() => {
    const handleInfiniteScroll = () => {
      if (loadingMore || !hasMore) return;
      const scrollPosition = window.innerHeight + window.scrollY;
      const threshold = document.body.offsetHeight - 300;
      if (scrollPosition >= threshold) {
        setPage((prev) => prev + 1);
      }
    };
    window.addEventListener('scroll', handleInfiniteScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleInfiniteScroll);
    };
  }, [loadingMore, hasMore]);

  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const isDarkMode = savedTheme === 'dark';
    setIsDark(isDarkMode);
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    document.documentElement.classList.toggle('dark', newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

  // Меняется стр => подгруз нового
  useEffect(() => {
    if (page === 1) return;
    loadGallery(page, true);
  }, [page]);

  // Начальное
  useEffect(() => {
    setPage(1);
    setHasMore(true);
    loadGallery(1, false);
    config.closeConnection();
    config.resetGameCreation();
    async function gameLoad() {
      if (!config.getProfile() && localStorage.getItem('access_token')) {
        await loadProfile();
      }
      const code = new URLSearchParams(window.location.search).get('code');
      const newProfile = config.getProfile();
      if (!newProfile && code) {
        config.navigateTo(config.Page.Login);
      }
      if (newProfile && code) {
        config.navigateTo(config.Page.Join, { name: newProfile.name, code, isHost: false });
      }
    }
    gameLoad();
  }, [searchTerm]);

  const handleSaveDeck = useCallback(async (deckId: string): Promise<void> => {
    if (!isLoggedIn) {
      config.navigateTo(config.Page.Login);
      return;
    }
    try {
      await config.validateToken();
      setSaveLoading(true);
      if (!deckId || deckId === 'undefined') {
        throw new Error(`Invalid deck ID provided', ${deckId}`);
      }
      const response = await fetch(`${config.HTTP_URL}/gallery/decks/${deckId}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to save deck: ${response.status} ${errorText}`);
      }
      const result = await response.json();
      // eslint-disable-next-line consistent-return
      return result.saved_deckid;
    } catch (error) {
      console.error('Failed to save deck:', error);
    } finally {
      setSaveLoading(false);
    }
  }, [isLoggedIn]);
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
    if (!isLoggedIn) { config.navigateTo(config.Page.Login); return; }
    if (!selectedDeck) return;
    config.addWords(selectedDeck.words);
    config.setDeckChoice(true);
    if (config.loadCreationState().aiGame) {
      config.navigateTo(config.Page.AiCreate);
    } else {
      config.navigateTo(config.Page.Create);
    }
  }, [selectedDeck]);

  return (
    <div className="bg-[#FAF6E9] dark:bg-[#1A1A1A] text-[#1E6DB9]">
      <div className="relative h-screen flex flex-col items-center justify-center px-6">
        <div className="absolute top-4 left-4 p-1 flex justify-between items-center">
          <a
            href="https://github.com/Team26SWP/InnoAlias"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub"
            className="text-gray-700 dark:text-white hover:opacity-80 transition"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 .5C5.73.5.5 5.74.5 12.01c0 5.1 3.29 9.43 7.86 10.96.58.11.79-.25.79-.56
                      0-.28-.01-1.02-.01-2-3.2.7-3.87-1.54-3.87-1.54-.53-1.35-1.3-1.7-1.3-1.7-1.06-.72.08-.71.08-.71
                      1.17.08 1.79 1.21 1.79 1.21 1.04 1.78 2.73 1.27 3.4.97.11-.76.41-1.28.74-1.57-2.55-.29-5.23-1.28-5.23-5.7
                      0-1.26.45-2.29 1.2-3.1-.12-.3-.52-1.49.11-3.1 0 0 .97-.31 3.17 1.18a11.03 11.03 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63
                      1.61.23 2.8.11 3.1.75.81 1.2 1.84 1.2 3.1 0 4.43-2.68 5.41-5.24 5.69.43.37.81 1.1.81 2.22 0 1.6-.01 2.89-.01 3.28 0
                      .31.21.68.8.56A10.51 10.51 0 0 0 23.5 12C23.5 5.74 18.27.5 12 .5z"
              />
            </svg>
          </a>
        </div>
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="absolute top-4 left-14 p-1.5 text-gray-700 dark:text-white hover:opacity-80 transition"
        >
          {isDark ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
              />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4V2m0 20v-2m8-8h2M2 12h2m14.14-7.07l1.42-1.42M4.44 19.56l1.42-1.42M19.56 19.56l-1.42-1.42M4.44 4.44l1.42 1.42M12 7a5 5 0 100 10 5 5 0 000-10z"
              />
            </svg>
          )}
        </button>

        <button
          type="button"
          aria-label={isLoggedIn ? 'Profile' : 'Log in'}
          onClick={isLoggedIn ? handleProfile : handleLogin}
          className="absolute top-4 right-4 bg-[#1E6DB9] text-[#FAF6DB] font-semibold px-4 py-2 rounded-full hover:opacity-90 transition"
        >
          {isLoggedIn ? 'Profile' : 'Log in'}
        </button>
        <h1 className="text-9xl font-bold font-adlam mb-8">alias</h1>
        <div className="flex gap-4 mb-8">
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
        {!showGallery && (
          <button
            type="button"
            onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
            aria-label="Scroll to gallery"
            className="absolute bottom-16 animate-bounce focus:outline-none"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="w-6 h-6 sm:w-8 sm:h-8 text-gray-700 dark:text-white opacity-70"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}

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
          {filtered.map((item) => (
            <button
              key={item._id}
              type="button"
              onClick={() => setSelectedDeck(item)}
              className="bg-gray-300 p-4 rounded-lg hover:opacity-90 transition text-left"
            >
              <h3 className="font-semibold mb-1">{item.name}</h3>
              <p className="text-xs text-gray-400">
                {item.words.length}
                {' '}
                terms
              </p>
              <p className="text-xs text-gray-400">Public Deck</p>
            </button>
          ))}
        </div>
        {loadingMore && (
          <div className="mt-6 block mx-auto text-center text-4xl text-[#1E6DB9] font-adlam">Loading more...</div>
        )}
        {!hasMore && filtered.length === 0 && (
          <div className="mt-6 block mx-auto text-center text-4xl text-[#1E6DB9] font-adlam">No decks found.</div>
        )}
      </div>
      <br />
      <br />
      <br />
      <br />
      <br />
      <br />
      <br />
      <br />
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
            <div className="bg-gray-300 rounded-lg max-w-md w-full p-6 space-y-4 z-60 onClick={(e) => e.stopPropagation()}">
              <h3 className="text-3xl font-bold">{selectedDeck.name}</h3>
              {profile && profile.isAdmin && (
              <p className="text-sm text-gray-600">
                Deck ID:
                {selectedDeck._id}
              </p>
              )}
              <p className="text-sm text-gray-600">
                Tags:
                {selectedDeck.tags.map((tag) => (
                  <li key={`tag-${tag}`}>
                    {tag}
                  </li>
                ))}
              </p>
              <ul className="max-h-48 overflow-y-auto list-disc list-inside space-y-1">
                {selectedDeck.words.map((word: string) => (
                  <li key={`${selectedDeck._id}-${word}`} className="text-xl">
                    {word}
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
                {isLoggedIn && selectedDeck && selectedDeck._id && (
                  <button
                    type="button"
                    onClick={() => {
                      const deckId = selectedDeck._id;
                      if (deckId) {
                        handleSaveDeck(deckId);
                      }
                    }}
                    disabled={saveLoading}
                    className="px-4 py-2 bg-[#1E6DB9] text-[#FAF6E9] rounded hover:opacity-90 transition"
                  >
                    {saveLoading ? 'Saving...' : 'Save to profile'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={useThisDeck}
                  className="px-4 py-2 bg-[#1E6DB9] text-[#FAF6E9] rounded hover:opacity-90 transition"
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
