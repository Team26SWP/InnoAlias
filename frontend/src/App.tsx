import { useState, useEffect } from 'react';
import HomePage from './components/Home';
import CreateGamePage from './components/CreateGame';
import JoinGamePage from './components/JoinGame';
import QuizPage from './components/Quiz';
import AiQuizPage from './components/AiQuiz';
import LobbyPage from './components/Lobby';
import LeaderboardPage from './components/Leaderboard';
import LoginPage from './components/Login';
import RegisterPage from './components/Register';
import ProfilePage from './components/Profile';
import EmailConfirmPage from './components/EmailConfirm';
import Host from './components/Host';
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
        return <CreateGamePage aiGame={false} />;
      case config.Page.AiCreate:
        return <CreateGamePage aiGame />;
      case config.Page.Lobby:
        return <LobbyPage />;
      case config.Page.Quiz:
        return <QuizPage />;
      case config.Page.AiGame:
        return <AiQuizPage />;
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
      case config.Page.Host:
        return <Host />;
      default:
        return <HomePage />;
    }
  };

  return <div className="App">{renderPage()}</div>;
}

export default App;
