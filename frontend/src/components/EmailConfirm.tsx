import React, { useState } from 'react';
import * as config from './config';

function EmailConfirm() {
  const [code, setCode] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Code entered:', code);

    config.navigateTo(config.Page.Home);
  };

  /*  const handleUpdateEmail = () => {
      config.navigateTo(config.Page.Register);
    };
  */
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FAF6E9] dark:bg-[#1A1A1A] px-4">
      <div className="w-full max-w-md bg-white p-8 rounded-xl shadow-md border-4">
        <h2 className="text-center text-2xl font-bold text-[#1E6DB9] font-adlam">
          Confirm your email address
        </h2>
        <p className="text-center text-gray-600 mb-6 text-sm">
          We have sent a code to
          {' '}
          <span className="text-black font-medium">{}</span>
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label htmlFor="code" className="block font-semibold text-black text-sm font-adlam">
            Enter code:
            <input
              id="code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full px-4 py-2 border-2 border-[#d9d9d9] rounded-full focus:outline-none focus:ring-2 focus:ring-[#1E6DB9]"
              required
            />
          </label>

          <button
            type="submit"
            className="w-full bg-[#1E6DB9] text-white font-bold py-2 rounded-full hover:opacity-90 font-adlam"
          >
            Continue
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-black">
          Didn’t get your email?
          {' '}
          <span className="text-[#1E6DB9] hover:underline cursor-pointer">Resend the code</span>
          {' '}
          or
          {' '}
          <span className="text-[#1E6DB9] hover:underline cursor-pointer"/* onClick={handleUpdateEmail} */> update your email address</span>
        </p>
      </div>
    </div>
  );
}

export default EmailConfirm;
