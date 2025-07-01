import React from 'react';
import * as config from './config';

export function Home() {
  const handleCreateGame = () => {
    if (!localStorage.getItem('access_token')) {
      config.navigateTo(config.Page.Login);
      return;
    }
    config.navigateTo(config.Page.Create);
  };

  const handleJoinGame = () => {
    if (!localStorage.getItem('access_token')) {
      config.navigateTo(config.Page.Login);
      return;
    }
    config.navigateTo(config.Page.Join);
  };

  const handleLogin = () => {
    config.navigateTo(config.Page.Login);
  };

  const handleProfile = () => {
    config.navigateTo(config.Page.Profile);
  };

  const loadProfile = async () => {
    const response = await fetch(`${config.HTTP_URL}/profile/me`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    });
    const profile = await response.json();
    if (response.ok) {
      config.setProfile(profile);
    }
  };

  React.useEffect(() => {
    config.closeConnection();
    config.resetGameCreation();
    if (!config.getProfile() && localStorage.getItem('access_token')) {
      loadProfile();
    }
  }, []);

  return (
    <div className="min-h-screen px-6 py-10 flex flex-col items-center justify-center bg-[#FAF6E9] text-[#1E6DB9] dark:bg-[#1A1A1A] dark:text-[#FAF6E9]">
      <button
        type="button"
        onClick={localStorage.getItem('access_token') ? handleProfile : handleLogin}
        className="absolute top-4 font-adlam right-4 bg-[#1E6DB9] text-[#FAF6E9] font-semibold px-4 py-2 rounded-full hover:opacity-90 transition"
      >
        {localStorage.getItem('access_token') ? <p>Profile</p> : <p>Log in</p> }
      </button>

      <h1 className="text-9xl font-bold font-adlam text-[#1E6DB9] mb-8">alias</h1>

      <div className="flex flex-col sm:flex-row gap-4">
        <button
          type="button"
          onClick={handleCreateGame}
          className="bg-[#1E6DB9] text-[#FAF6E9] font-adlam px-6 py-3 rounded-lg text-lg font-medium hover:opacity-90 transition"
        >
          Create game
        </button>
        <button
          type="button"
          onClick={handleJoinGame}
          className="bg-[#FAF6E9] dark:bg-[#1A1A1A] border border-[#1E6DB9] font-adlam text-[#1E6DB9] px-6 py-3 rounded-lg text-lg font-medium"
        >
          Join the game
        </button>
      </div>
    </div>
  );
}

export default Home;
