import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../style/Home.css';
import characterImg from '../assets/character.png';

const Home: React.FC = () => {
  const navigate = useNavigate();

  const handleCreateGame = () => {
    navigate('/create_game');
  };

  const handleJoinGame = () => {
    navigate('/join_game');
  };

  return (
    <div className ="home-wrapper">
    <div className="home-container">
      <h1>ALIAS</h1>
      <h2>"Alias" is the name of a popular word explanation game, often played in teams. The objective of the game is
          to have your teammates guess words you are describing without actually saying the word itself.</h2>
      <div className="home-options">
        <button onClick={handleCreateGame} className="create-button">
          Create Game
        </button>
        <button onClick={handleJoinGame} className="join-button">
          Join Game
        </button>
      </div>
      </div>
      <div className="home-image">
    <img src={characterImg} alt="Alias character" />
  </div>
    </div>
  );
};

export default Home; 