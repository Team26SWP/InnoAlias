import React, { useState, useEffect } from 'react';
import Home from './components/Home';
import CreateGame from './components/CreateGame';
import JoinGame from './components/JoinGame';
import Quiz from './components/Quiz';
import Lobby from './components/Lobby';
import Leaderboard from './components/Leaderboard';
import * as Config from './components/Config';

function App() {
  const [currentPage, setCurrentPage] = useState<Config.Page>(Config.Page.Home);

  useEffect(() => {
    Config.registerSetCurrentPage(setCurrentPage);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case Config.Page.Home:
        return <Home />;
      case Config.Page.Join:
        return <JoinGame />;
      case Config.Page.Create:
        return <CreateGame />;
      case Config.Page.Lobby:
        return <Lobby />;
      case Config.Page.Quiz:
        return <Quiz />;
      case Config.Page.Leaderboard:
        return <Leaderboard />;
      case Config.Page.Results:
        return null;
      default:
        return <Home />;
    }
  };

  return <div className="App">{renderPage()}</div>;
}

export default App;
