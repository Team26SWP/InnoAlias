import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Email:", email);
    console.log("Password:", password);
  };

  const handleSignUp = () => {
    navigate('/register');
  };

  return (
    <div className="min-h-screen flex items-center dark:bg-[#1A1A1A] justify-center bg-[#FAF6E9] font-adlam px-4">
      <form
        onSubmit={handleSubmit}
        className="bg-white shadow-md rounded-xl px-8 py-10 w-full max-w-md"
      >
        <h2 className="text-2xl text-center font-bold text-[#1E6DB9] mb-6">
          Log in to your account
        </h2>

        <label className="block text-[#1E6DB9] font-semibold mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full mb-4 px-4 py-2 border-2 text-[#1E6DB9] border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
        />

        <label className="block text-[#1E6DB9] font-semibold mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full mb-2 px-4 py-2 text-[#1E6DB9] border-2 border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
        />

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
          Don’t have an account?{' '}
          <span
            onClick={handleSignUp}
            className="text-[#1E6DB9] font-semibold cursor-pointer hover:underline"
          >
            Sign up
          </span>
        </div>
      </form>
    </div>
  );
};

export default Login;
