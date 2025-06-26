import React from "react";
import * as config from './config';

const Home: React.FC = () => {
  const handleCreateGame = () => {
    config.navigateTo(config.Page.Create)
  };

  const handleJoinGame = () => {
    config.navigateTo(config.Page.Join)
  };

  const handleLogin = () => {
  config.navigateTo(config.Page.Login)
  };


  React.useEffect(() => {
    config.closeConnection();
  }, [])

return (
    <div className="min-h-screen px-6 py-10 flex flex-col items-center justify-center bg-[#FAF6E9] text-[#1E6DB9] dark:bg-[#1A1A1A] dark:text-[#FAF6E9]">
      <button
        onClick={handleLogin}
        className="absolute top-4 font-adlam right-4 bg-[#1E6DB9] text-[#FAF6E9] font-semibold px-4 py-2 rounded-full hover:opacity-90 transition"
      >
        Log in
      </button>
      <h1 className="text-9xl font-bold font-adlam text-[#1E6DB9] mb-8">alias</h1>

      <div className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={handleCreateGame}
          className="bg-[#1E6DB9] text-[#FAF6E9] font-adlam px-6 py-3 rounded-lg text-lg font-medium hover:opacity-90 transition"
        >
          Create game
        </button>
        <button
          onClick={handleJoinGame}
          className="bg-[#FAF6E9] dark:bg-[#1A1A1A] border border-[#1E6DB9] font-adlam text-[#1E6DB9] px-6 py-3 rounded-lg text-lg font-medium"
        >
          Join the game
        </button>
      </div>
    </div>
  );
};


export default Home; 