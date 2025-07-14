import React, { useState } from 'react';
import * as config from './config';

export interface RegisterForm {
  name: string;
  surname: string;
  email: string;
  password: string;
}

function Register() {
  const [form, setForm] = useState<RegisterForm>({
    name: '',
    surname: '',
    email: '',
    password: '',
  });
  const [error, setError] = useState <string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const response = await fetch(`${config.HTTP_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: form.name,
          surname: form.surname,
          email: form.email,
          password: form.password,
        }),
      });

      if (!response.ok) {
        if (response.status === 400) {
          setError('Email already registered');
        } else {
          setError(`Error: ${response.status} ${response.statusText}`);
        }
        return;
      }
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('token_type', data.token_type);
      localStorage.setItem('refresh_token', data.refresh_token);

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
        setError('Failed to fetch profile after registration');
      }

      // config.navigateTo(config.Page.EmailConfirm);
      config.navigateTo(config.Page.Home);
    } catch (err) {
      setError('An unexpected error occurred. Please try again later.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FAF6E9] dark:bg-[#1A1A1A] px-4">
      <button
        type="button"
        onClick={() => config.navigateTo(config.Page.Home)}
        className="absolute top-4 text-xl left-4 text-[#1E6DB9] hover:underline"
      >
        ←Back to main
      </button>
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold text-center text-[#1E6DB9] mb-6 font-adlam">
          Create account
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4" name="register">
          <div className="flex gap-4">
            <div className="flex-1">
              <label id="name" htmlFor="name" className="block text-[#1E6DB9] font-semibold mb-1 font-adlam">
                Name
                <input
                  type="text"
                  name="name"
                  aria-labelledby="name"
                  value={form.name}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border-2 border-[#d9d9d9] rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
                  required
                />
              </label>
            </div>
            <div className="flex-1">
              <label id="surname" htmlFor="surname" className="block text-[#1E6DB9] font-semibold mb-1 font-adlam">
                Surname
                <input
                  type="text"
                  name="surname"
                  aria-labelledby="surname"
                  value={form.surname}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border-2 border-[#d9d9d9] rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
                  required
                />
              </label>
            </div>
          </div>
          <div>
            <label id="email" htmlFor="email" className="block text-[#1E6DB9] font-semibold mb-1 font-adlam">
              Your Email
              <input
                type="email"
                name="email"
                aria-labelledby="email"
                value={form.email}
                onChange={handleChange}
                className="w-full px-4 py-2 border-2 border-[#d9d9d9] rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
                required
              />
            </label>
          </div>
          <div>
            <label id="password" htmlFor="password" className="block text-[#1E6DB9] font-semibold mb-1 font-adlam">
              Password
              <input
                type="password"
                name="password"
                aria-labelledby="password"
                value={form.password}
                onChange={handleChange}
                className="w-full px-4 py-2 border-2 border-[#d9d9d9] rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
                required
              />
            </label>
          </div>
          {error && (
            <p className="text-red-500 text-center font-semibold">{error}</p>
          )}
          <button
            type="submit"
            className="w-full bg-[#1E6DB9] text-white font-bold py-2 rounded-full mt-4 hover:opacity-90 font-adlam"
          >
            Create
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-black">
          Already have an account?
          {' '}
          <button type="button" onClick={() => config.navigateTo(config.Page.Login)} className="text-[#1E6DB9] hover:underline">
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}

export default Register;
