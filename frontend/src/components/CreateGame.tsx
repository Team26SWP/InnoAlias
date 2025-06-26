import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import socketConfig from "./config";
class Settings {
  time: number;
  deckLimit: number;
  attemptsLimit: number;
  answersLimit: number;
  constructor(time: number, deck: number, attempts: number, answers: number) {
    this.time = time;
    this.deckLimit = deck;
    this.attemptsLimit = attempts;
    this.answersLimit = answers;
  }
}

interface Deck {
  name: string;
  cards: string[];
}

const CreateGame: React.FC = () => {
  const [words, setWords] = useState<string[]>([]);
  const [currentWord, setCurrentWord] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [hostName, setHostName] = useState<string>("");
  const [decks, setDecks] = useState<Deck[]>([]);

  const settings = useRef<Settings>(new Settings(60, 0, 3, 1));
  const navigate = useNavigate();

  useEffect(() => {
    const cookies = document.cookie.replaceAll("[", "").replaceAll("]", "");
    if (!cookies) return;
    var deckStrings: string[] = cookies.split(";");
    var supplementaryArray: Deck[] = [];
    for (let i = 0; i < deckStrings.length; i++) {
      const parsedString = deckStrings[i].split("=");
      supplementaryArray.push({ name: parsedString[0], cards: parsedString[1].split(",") });
    }
    setDecks(supplementaryArray);
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = currentWord.trim();
    if (trimmed) {
      setWords([...words, trimmed.toLowerCase()]);
      setCurrentWord('');
      setError(null);
    }
  };

  const parse = (text: string) => {
    const lines = text
      .split(/\r?\n/)
      .map(l => l.trim())
      .filter(l => l.length);
    setWords(ws => [...ws, ...lines]);
  };

  const fileSubmit = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) file.text().then(parse);
  };

  const handleStartGame = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${socketConfig.HTTP_URL}/game/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          remaining_words: words,
          words_amount: (settings.current.deckLimit === 0) ? words.length : settings.current.deckLimit,
          time_for_guessing: settings.current.time,
          tries_per_player: settings.current.attemptsLimit,
          right_answers_to_advance: settings.current.answersLimit
        }),
      });

      if (!res.ok) throw new Error();
      const data = await res.json();
      navigate(`/lobby?code=${data.id}&name=${hostName}&host=true`);
    } catch {
      setError('Failed to create game. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = () => {
    const minutes = document.getElementById("minutes");
    const seconds = document.getElementById("seconds");
    const deckLimit = document.getElementById("deck-length");
    const attemptLimit = document.getElementById("attempts");
    const answerLimit = document.getElementById("answers");
    if (minutes instanceof HTMLInputElement && seconds instanceof HTMLInputElement && deckLimit instanceof HTMLInputElement && attemptLimit instanceof HTMLInputElement && answerLimit instanceof HTMLInputElement) {
      settings.current.time = parseInt((minutes.value !== "") ? minutes.value : "1") * 60 + parseInt((seconds.value !== "") ? seconds.value : "0");
      if (settings.current.time === 0) settings.current.time = 1;
      settings.current.deckLimit = parseInt((deckLimit.value !== "") ? deckLimit.value : "0");
      settings.current.attemptsLimit = parseInt((attemptLimit.value !== "") ? attemptLimit.value : "3");
      settings.current.answersLimit = parseInt((answerLimit.value !== "") ? answerLimit.value : "1");
    }
    setShowSettings(false);
  }

  const loadDeck = () => {
    const selector = document.getElementById("selector");
    if (!(selector instanceof HTMLSelectElement)) return;
    const cards = selector.value;
    if (cards === "") { return; }
    setWords(words.concat(cards.split(",")));
  }

 return (
    <div className="min-h-screen bg-[#FAF6E9] text-[#1E6DB9] font-adlam flex flex-col items-center dark:bg-[#1A1A1A] pt-10 px-6">
      <h1 className="text-4xl font-bold mb-10 text-center">Create Word Game</h1>

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

          <h2 className="text-xl font-bold mb-4">Added Words ({words.length}):</h2>
          <div className="grid grid-cols-5 md:grid-cols-7 gap-4">
            {words.map((word, i) => (
              <span key={i} className="bg-[#E2E2E2] text-[#1E6DB9] px-4 py-2 rounded-full text-center text-sm font-adlam">
                {word}
              </span>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-4 min-w-[160px]">
          <button onClick={handleSubmit} className="bg-[#1E6DB9] text-[#FAF6E9] px-4 py-5 rounded-md font-adlam">Add</button>
          <label className="bg-[#1E6DB9] text-[#FAF6E9] px-8 py-3 rounded-md text-center font-adlam cursor-pointer">
            Import via txt
            <input type="file" className="hidden" onChange={fileSubmit} />
          </label>
          <button onClick={loadDeck} className="bg-[#1E6DB9] text-[#FAF6E9] px-8 py-3 rounded-md font-adlam">Saved Desks</button>
          <button onClick={() => setShowSettings(true)} className="bg-[#DBD9D1] text-[#1E6DB9] px-4 py-3 rounded-md font-adlam">Settings</button>
        </div>
      </div>

      <button
        onClick={handleStartGame}
        disabled={words.length === 0 || !hostName || isLoading}
        className="mt-12 px-10 py-4 bg-[#1E6DB9] text-[#FAF6E9] rounded-lg font-adlam text-lg disabled:bg-gray-400"
      >
        {isLoading ? 'Creating Game...' : 'Start Game'}
      </button>

      {showSettings && (
  <div className="fixed inset-0 bg-black backdrop-blur-sm bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-[#DBD9D1] text-[#1E6DB9] rounded-lg px-12 py-10 w-[90%] max-w-2xl relative font-adlam">
      <button
        onClick={() => setShowSettings(false)}
        className="absolute top-4 left-4 text-2xl"
      >
        ✕
      </button>

      <div className="flex flex-col gap-4 mt-10">
        <div className="flex items-center justify-between gap-2">
          <span className="font-bold w-36">Time:</span>
          <div className="flex items-center gap-2">
            <input
              id="minutes"
              type="number"
              placeholder=""
              className="w-14 p-2 rounded-md"
            />
            <span className="text-sm">min</span>
            <input
              id="seconds"
              type="number"
              placeholder=""
              className="w-14 p-2 rounded-md"
            />
            <span className="text-sm">sec</span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span className="font-bold w-36">Deck limit:</span>
          <div className="flex items-center gap-2">
            <input
              id="deck-length"
              type="number"
              className="w-14 p-2 rounded-md"
            />
            <span className="text-sm">cards</span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span className="font-bold w-36">Limit of attempts:</span>
          <div className="flex items-center gap-2">
            <input
              id="attempts"
              type="number"
              className="w-14 p-2 rounded-md"
            />
            <span className="text-sm">tries</span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span className="font-bold w-36">Limit of correct answers:</span>
          <div className="flex items-center gap-2">
            <input
              id="answers"
              type="number"
              className="w-14 p-2 rounded-md"
            />
            <span className="text-sm">players</span>
          </div>
        </div>

        <button
          onClick={saveSettings}
          className="bg-[#1E6DB9] text-white py-2 mt-4 rounded-md"
        >
          Save
        </button>
      </div>
    </div>
  </div>
)}


    </div>
  );
};

export default CreateGame;
