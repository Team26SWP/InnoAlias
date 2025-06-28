import { useState, useEffect } from 'react';
import HomePage from './components/Home';
import CreateGamePage from './components/CreateGame';
import JoinGamePage from './components/JoinGame';
import QuizPage from './components/Quiz';
import LobbyPage from './components/Lobby';
import LeaderboardPage from './components/Leaderboard';
import LoginPage from './components/Login';
import RegisterPage from './components/Register';
import ProfilePage from './components/Profile';
import EmailConfirmPage from './components/EmailConfirm';
import * as config from './components/config';

function App() {
  const [currentPage, setCurrentPage] = useState<config.Page>(config.Page.Home);

  useEffect(() => {
    config.registerSetCurrentPage(setCurrentPage);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case config.Page.Home:
        return <HomePage />;
      case config.Page.Join:
        return <JoinGamePage />;
      case config.Page.Create:
        return <CreateGamePage />;
      case config.Page.Lobby:
        return <LobbyPage />;
      case config.Page.Quiz:
        return <QuizPage />;
      case config.Page.Leaderboard:
        return <LeaderboardPage />;
      case config.Page.Login:
        return <LoginPage />;
      case config.Page.Register:
        return <RegisterPage />;
      case config.Page.Profile:
        return <ProfilePage />;
      case config.Page.EmailConfirm:
        return <EmailConfirmPage />;
      default:
        return <HomePage />;
    }
  };

  return <div className="App">{renderPage()}</div>;
}

export default App;
