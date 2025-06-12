import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../style/Home.css';
import characterImg from '../assets/character.png';

/**
 * Home Component
 * 
 * This is the landing page component that serves as the main entry point for the Alias game.
 * It provides two main options for users:
 * 1. Create a new game
 * 2. Join an existing game
 * 
 * The component includes a brief description of the game and a character image
 * for visual appeal.
 */
const Home: React.FC = () => {
  // Hook for programmatic navigation between routes
  const navigate = useNavigate();

  /**
   * Handles navigation to the game creation page
   * Triggered when user clicks the "Create Game" button
   */
  const handleCreateGame = () => {
    navigate('/create_game');
  };

  /**
   * Handles navigation to the game joining page
   * Triggered when user clicks the "Join Game" button
   */
  const handleJoinGame = () => {
    navigate('/join_game');
  };

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
          <button onClick={handleCreateGame} className="create-button">
            Create Game
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