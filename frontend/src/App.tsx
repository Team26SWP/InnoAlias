import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import CreateGame from './components/CreateGame';
import JoinGame from './components/JoinGame';
import Quiz from './components/Quiz';
import Results from './components/Results';
import Lobby from './components/Lobby';
import Leaderboard from './components/Leaderboard';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/create_game" element={<CreateGame />} />
          <Route path="/join_game/:code?" element={<JoinGame />} />
          <Route path="/game/:gameId" element={<Quiz />} />
          <Route path="/results/:gameId" element={<Results />} />
          <Route path="/lobby/:gameId" element={<Lobby />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
