import React, { useState } from 'react';
import * as config from './config';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${config.HTTP_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),

      });

      if (!response.ok) {
        if (response.status === 401) {
          setError('Invalid email or password');
        } else if (response.status === 400) {
          setError('Wrong email or password');
        } else {
          setError(`Error: ${response.status} ${response.statusText}`);
        }
        return;
      }
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('token_type', data.token_type);
      localStorage.setItem('refresh_token', data.refresh_token);
      config.navigateTo(config.Page.Home);
      try {
        const token = data.access_token;
        const profileResponse = await fetch(`${config.HTTP_URL}/profile/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (profileResponse.ok) {
          const profileData = await profileResponse.json();
          config.setProfile(profileData);
        }
      } catch (profileErr) {
        setError('Failed to fetch profile after login');
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again later.');
    }
  };

  return (
    <div className="relative min-h-screen flex items-center dark:bg-[#1A1A1A] justify-center bg-[#FAF6E9] font-adlam px-4">
      <button
        type="button"
        onClick={() => config.navigateTo(config.Page.Home)}
        className="absolute top-4 text-xl left-4 text-[#1E6DB9] hover:underline"
      >
        ←Back to main
      </button>
      <form
        onSubmit={handleSubmit}
        className="bg-white shadow-md rounded-xl px-8 py-10 w-full max-w-md"
      >
        <h2 className="text-2xl text-center font-bold text-[#1E6DB9] mb-6">
          Log in to your account
        </h2>

        <label htmlFor="email" className="block text-[#1E6DB9] mb-1">
          Email
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full mb-4 px-4 py-2 border-2 text-[#1E6DB9] border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
          />
        </label>

        <label htmlFor="password" className="block text-[#1E6DB9] mb-1">
          Password
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full mb-2 px-4 py-2 text-[#1E6DB9] border-2 border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
          />
        </label>

        <div className="text-sm text-right text-[#1E6DB9] mb-6 cursor-pointer hover:underline">
          Forgot password?
        </div>

        <button
          type="submit"
          className="w-full bg-[#1E6DB9] text-[#FAF6E9] py-3 rounded-full font-bold hover:opacity-90 transition"
        >
          Continue
        </button>

        <div className="text-center mt-4 text-sm text-[#1A1A1A]">
          Don’t have an account?
          {' '}
          <button
            type="button"
            onClick={() => config.navigateTo(config.Page.Register)}
            className="text-[#1E6DB9] cursor-pointer hover:underline"
          >
            Sign up
          </button>
        </div>
        {error && (
          <p className="text-red-500 text-center">{error}</p>
        )}
      </form>
    </div>
  );
}

export default Login;
