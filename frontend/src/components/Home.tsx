import React, { useEffect, useState } from "react";
import '../style/Home.css';
import * as Config from './Config';
import characterImg from '../assets/character.png';

const Home: React.FC = () => {
  const handleCreateGame = () => {
    Config.navigateTo(Config.Page.Create)
  };

const handleJoinGame = () => {
  Config.navigateTo(Config.Page.Join)
};

  React.useEffect(() => {
    Config.closeConnection();
  }, [])
  return (
    <div className="home-wrapper">
      {/* Main container for the home page content */}
      <div className="home-container">
        {/* Game title */}
        <h1>ALIAS</h1>
        
        {/* Game description */}
        <h2>"Alias" is the name of a popular word explanation game, often played in teams. The objective of the game is
            to have your teammates guess words you are describing without actually saying the word itself.</h2>
        
        {/* Navigation buttons container */}
        <div className="home-options">
          <button onClick={handleCreateGame} className="create-home-button">
            Create Game
          </button>
          <button onClick={handleJoinGame} className="join-home-button">
            Join Game
          </button>
        </div>
      </div>

      {/* Character image section */}
      <div className="home-image">
        <img src={characterImg} alt="Alias character" />
      </div>
    </div>
  );
};

export default Home; 