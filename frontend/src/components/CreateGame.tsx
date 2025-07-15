import React, { useState, useRef, useEffect } from 'react';
import * as config from './config';

interface CreateProp {
  aiGame: boolean;
}

export function CreateGame(prop: CreateProp) {
  const [words, setWords] = useState<string[]>(config.loadCreationState().words);
  const [currentWord, setCurrentWord] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [hostId, setHostId] = useState<string>('');
  const [settings] = useState<config.Settings>(config.loadCreationState().settings);
  const socketRef = useRef<WebSocket | null>(null);
  const { aiGame } = prop;

  useEffect(() => {
    const profile = config.getProfile();
    config.setDeckChoice(false);
    if (profile) {
      setHostId(profile.id);
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = currentWord.trim();
    for (let i = 0; i < words.length; i += 1) {
      if (words[i].toLowerCase() === trimmed.toLowerCase()) {
        return;
      }
    }
    if (trimmed) {
      setWords([...words, trimmed]);
      setCurrentWord('');
    }
  };

  const parse = (text: string) => {
    const lines = text
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter((l) => l.length);
    setWords((ws) => [...ws, ...lines]);
  };

  const fileSubmit = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) file.text().then(parse);
  };

  const loadDeck = () => {
    config.saveCreationState(settings, words, aiGame);
    config.setDeckChoice(true);
    config.navigateTo(config.Page.Profile);
  };

  function downToRange(num: number, minimum: number, maximum: number) {
    if (num > maximum) { return maximum; }
    if (num < minimum) { return minimum; }
    return num;
  }

  const deleteWord = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!(e.target instanceof HTMLElement)) { return; }
    const deleted = e.target.textContent;
    setWords(words.filter((word) => word !== deleted));
  };

  const handleCreateGame = async () => {
    setIsLoading(true);
    try {
      let response: Response;
      if (!aiGame) {
        response = await fetch(`${config.HTTP_URL}/game/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            host_id: hostId,
            deck: words,
            words_amount: (settings.deckLimit === 0) ? words.length
              : settings.deckLimit,
            time_for_guessing: settings.time,
            tries_per_player: settings.attemptsLimit,
            right_answers_to_advance: settings.answersLimit,
            rotate_masters: settings.rotateMasters,
            number_of_teams: settings.numberOfTeams,
          }),
        });
      } else {
        response = await fetch(`${config.HTTP_URL}/aigame/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            deck: words,
            settings: {
              time_for_guessing: settings.time,
              word_amount: settings.deckLimit,
            },
          }),
        });
      }

      if (!response.ok) throw new Error();
      const data = await response.json();
      let gameCode: string;
      if (aiGame) {
        gameCode = data.game_id;
      } else {
        gameCode = data.id;
      }

      let socket: WebSocket;
      if (!aiGame) {
        socket = config.connectSocketHost(hostId, gameCode);
      } else {
        socket = config.connectSocketAi(gameCode);
      }
      socketRef.current = socket;

      if (!aiGame) {
        socket.onopen = () => {
          config.setRotation(settings.rotateMasters);
          config.navigateTo(config.Page.Lobby, { name: hostId, code: gameCode, isHost: true });
        };
      } else {
        socket.onmessage = (msg) => {
          config.setInitialAiState(JSON.parse(msg.data));
          config.navigateTo(config.Page.AiGame);
        };
      }

      socket.onerror = () => {
        setIsLoading(false);
      };
    } catch {
      setIsLoading(false);
    }
  };

  const saveSettings = () => {
    const minutes = document.getElementById('minutes');
    const seconds = document.getElementById('seconds');
    const deckLimit = document.getElementById('deck-length');
    const attemptLimit = document.getElementById('attempts');
    const answerLimit = document.getElementById('answers');
    const numberTeams = document.getElementById('teams');
    const rotation = document.getElementById('different-master');
    if (minutes instanceof HTMLInputElement && seconds instanceof HTMLInputElement
      && deckLimit instanceof HTMLInputElement && attemptLimit instanceof HTMLInputElement
      && answerLimit instanceof HTMLInputElement && rotation instanceof HTMLInputElement
      && numberTeams instanceof HTMLInputElement) {
      settings.time = parseInt((minutes.value !== '') ? minutes.value : minutes.placeholder, 10) * 60
        + parseInt((seconds.value !== '') ? seconds.value : seconds.placeholder, 10);
      if (settings.time === 0) settings.time = 1;
      settings.deckLimit = parseInt((deckLimit.value !== '') ? deckLimit.value : '0', 10);
      settings.attemptsLimit = parseInt((attemptLimit.value !== '') ? attemptLimit.value : attemptLimit.placeholder, 10);
      settings.answersLimit = parseInt((answerLimit.value !== '') ? answerLimit.value : answerLimit.placeholder, 10);
      settings.numberOfTeams = parseInt((numberTeams.value !== '') ? numberTeams.value : numberTeams.placeholder, 10);
      settings.rotateMasters = rotation.checked;
    }
    setShowSettings(false);
  };

  return (
    <div className="min-h-screen bg-[#FAF6E9] text-[#1E6DB9] font-adlam flex flex-col items-center dark:bg-[#1A1A1A] pt-10 px-6">
      <button
        type="button"
        onClick={() => config.navigateTo(config.Page.Home)}
        className="absolute top-4 text-xl left-4 text-[#1E6DB9] hover:underline"
      >
        ←Back to main
      </button>
      <h1 className="text-4xl font-bold mb-10 text-center">Create Game</h1>

      <div className="flex flex-col md:flex-row gap-8 w-full max-w-6xl items-start">
        <div className="flex-1 w-full">
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Enter a word(-s)........"
              value={currentWord}
              onChange={(e) => setCurrentWord(e.target.value)}
              className="w-full bg-[#D9D9D9] placeholder:text-[#7d7d7d] text-[#1E6DB9] px-6 py-4 text-lg rounded-full outline-none font-adlam mb-10"
            />
          </form>

          <h2 className="text-xl font-bold mb-4">
            Added Words (
            {words.length}
            ):
          </h2>
          <div className="grid grid-cols-5 md:grid-cols-7 gap-4">
            {words.map((word) => (
              <button type="button" key={word} onClick={deleteWord}>
                <span key={word} className="bg-[#E2E2E2] text-[#1E6DB9] px-4 py-2 rounded-full text-center text-sm font-adlam">
                  {word}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-4 min-w-[160px]">
          <button type="button" onClick={handleSubmit} className="bg-[#1E6DB9] text-[#FAF6E9] px-4 py-5 rounded-md font-adlam">Add</button>
          <label htmlFor="file-submit" className="bg-[#1E6DB9] text-[#FAF6E9] px-8 py-3 rounded-md text-center font-adlam cursor-pointer">
            Import via txt
            <input type="file" className="hidden" onChange={fileSubmit} id="file-submit" accept=".txt" />
          </label>
          <button type="button" onClick={loadDeck} className="bg-[#1E6DB9] text-[#FAF6E9] px-8 py-3 rounded-md font-adlam">Saved Decks</button>
          <button type="button" onClick={() => setShowSettings(true)} className="bg-[#DBD9D1] text-[#1E6DB9] px-4 py-3 rounded-md font-adlam">Settings</button>
        </div>
      </div>

      <button
        type="button"
        onClick={handleCreateGame}
        disabled={words.length === 0 || isLoading}
        className="mt-12 px-10 py-4 bg-[#1E6DB9] text-[#FAF6E9] rounded-lg font-adlam text-lg disabled:bg-gray-400"
      >
        {isLoading ? 'Creating Game...' : 'Create Game'}
      </button>

      {showSettings && (
      <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-[#DBD9D1] text-[#1E6DB9] rounded-lg px-6 py-10 w-[90%] max-w-2xl relative">
          <button
            type="button"
            onClick={() => setShowSettings(false)}
            className="absolute top-4 left-4 text-2xl"
          >
            ✕
          </button>

          <div className="grid md:grid-cols-[35ch_auto_auto_minmax(0,1fr)] lg:grid-cols-[40ch_auto_auto_minmax(0,1fr)] gap-x-2 gap-y-4 items-center">
            <span className="font-bold text-left">Time for one word:</span>
            <input
              id="minutes"
              type="number"
              placeholder={Math.floor(settings.time / 60).toString()}
              className="w-12 p-2 rounded-md"
              onChange={(e) => {
                e.target.value = downToRange(Number.parseInt(e.target.value, 10), 0, 59)
                  .toString();
              }}
            />
            <span className="text-sm">min</span>
            <div className="flex items-center gap-2">
              <input
                id="seconds"
                type="number"
                placeholder={String(settings.time % 60)}
                className="w-12 p-2 rounded-md"
                onChange={(e) => {
                  e.target.value = downToRange(Number.parseInt(e.target.value, 10), 0, 59)
                    .toString();
                }}
              />
              <span className="text-sm">sec</span>
            </div>

            <span className="font-bold text-left">Cards in game (leave empty for all cards):</span>
            <div />
            <div />
            <div className="flex items-center gap-2">
              <input
                id="deck-length"
                type="number"
                placeholder={settings.deckLimit === 0 ? '' : settings.deckLimit.toString()}
                className="w-12 p-2 rounded-md"
              />
              <span className="text-sm">cards</span>
            </div>
            {!aiGame && (
              <>
                <span className="font-bold text-left">Amount Of Guesses:</span>
                <div />
                <div />
                <div className="flex items-center gap-2">
                  <input
                    id="attempts"
                    type="number"
                    placeholder={String(settings.attemptsLimit)}
                    className="w-12 p-2 rounded-md"
                    onChange={(e) => {
                      e.target.value = String(
                        downToRange(parseInt(e.target.value, 10), 1, 100),
                      );
                    }}
                  />
                  <span className="text-sm">guesses</span>
                </div>

                <span className="font-bold text-left">Limit Of Correct Answers For The Card:</span>
                <div />
                <div />
                <div className="flex items-center gap-2">
                  <input
                    id="answers"
                    type="number"
                    placeholder={String(settings.answersLimit)}
                    className="w-12 p-2 rounded-md"
                    onChange={(e) => {
                      e.target.value = downToRange(Number.parseInt(e.target.value, 10), 1, 100)
                        .toString();
                    }}
                  />
                  <span className="text-sm">answers</span>
                </div>

                <span className="font-bold text-left">Number of teams:</span>
                <div />
                <div />
                <div className="flex items-center gap-2">
                  <input
                    id="teams"
                    type="number"
                    placeholder={settings.numberOfTeams.toString()}
                    className="w-12 p-2 rounded-md"
                    onChange={(e) => {
                      e.target.value = downToRange(Number.parseInt(e.target.value, 10), 1, 100)
                        .toString();
                    }}
                  />
                  <span className="text-sm">teams</span>
                </div>
              </>
            )}
          </div>

          {!aiGame && (
            <div className="flex items-center gap-5 mt-10">
              <label htmlFor="single-master" className="flex items-center gap-2">
                <input type="radio" id="single-master" name="master-mode" value="single" defaultChecked={!settings.rotateMasters} />
                <span className="font-bold w-36">Single Master</span>
              </label>
              <label htmlFor="different-master" className="flex items-center gap-2">
                <input type="radio" id="different-master" name="master-mode" value="different" defaultChecked={settings.rotateMasters} />
                <span className="font-bold w-36">Different Masters</span>
              </label>
            </div>
          )}

          <div className="flex justify-center w-full mt-6">
            <button
              type="button"
              onClick={saveSettings}
              className="bg-[#1E6DB9] text-white px-8 py-4 rounded-md text-lg w-64"
            >
              Save
            </button>
          </div>
        </div>
      </div>
      )}
    </div>
  );
}

export default CreateGame;
