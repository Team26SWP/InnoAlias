import React, { useState } from 'react';
import '../style/Quiz.css';

const Quiz: React.FC = () => {
  const [word, setWord] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Submitted word:', word);
    setWord('');
  };

  return (
    <div className="quiz-container">
      <div className="question-card">
        <h2>Enter a word:</h2>
        <form onSubmit={handleSubmit} className="guess-form">
          <input
            type="text"
            value={word}
            onChange={(e) => setWord(e.target.value)}
            placeholder="Type a word..."
            className="guess-input"
          />
          <button type="submit" className="guess-button">
            Submit
          </button>
        </form>
      </div>
    </div>
  );
};

export default Quiz; 