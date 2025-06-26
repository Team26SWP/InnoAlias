import React, { useState, useEffect } from 'react';
import Home from './components/Home';
import CreateGame from './components/CreateGame';
import JoinGame from './components/JoinGame';
import Quiz from './components/Quiz';
import Lobby from './components/Lobby';
import Leaderboard from './components/Leaderboard';
import Login from './components/Login';
import Register from './components/Register';
import EmailConfirm from './components/EmailConfirm';
import * as config from './components/config';

function App() {
  const [currentPage, setCurrentPage] = useState<config.Page>(config.Page.Home);

  useEffect(() => {
    config.registerSetCurrentPage(setCurrentPage);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case config.Page.Home:
        return <Home />;
      case config.Page.Join:
        return <JoinGame />;
      case config.Page.Create:
        return <CreateGame />;
      case config.Page.Lobby:
        return <Lobby />;
      case config.Page.Quiz:
        return <Quiz />;
      case config.Page.Leaderboard:
        return <Leaderboard />;
      case config.Page.Login:
        return <Login />;
      case config.Page.Register:
        return <Register />;
      case config.Page.EmailConfirm:
        return <EmailConfirm />;
      default:
        return <Home />;
    }
  };

  return <div className="App">{renderPage()}</div>;
}

export default App;
