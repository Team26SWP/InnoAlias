import React, { useEffect, useState } from "react";
import * as config from './config';

const Profile: React.FC = () => {
  const [profile, setProfile] = useState<config.UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const collections = ["MathAnal", "SSAD", "Comparch", "I am Matvei"];
  const tags = ["Math", "CS", "Engineering","Russian","VS code","Agla","English","UX&UI","3D", "AI", "ML", "Data", "Theory","Backend", "TCS", "GB"];

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('access_token');
        console.log(localStorage.getItem('access_token'));
        const response = await fetch(`${config.HTTP_URL}/profile/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          setError('Failed to fetch profile.');
          setLoading(false);
          return;
        }
        const data = await response.json();
        setProfile(data);
        config.setProfile(data);
      } catch (err) {
        setError('An unexpected error occurred.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!profile) {
    return <div>No profile data available</div>;
  }

  return (
    <div className="min-h-screen bg-[#FAF6E9] px-6 py-10 font-adlam text-[#1E6DB9]">
      <h1 className="text-4xl font-bold mb-6">Profile</h1>

      <div className="flex items-center mb-10 gap-6">
        <div className="w-36 h-36 bg-gray-300 rounded-full" />
        <div>
          <h2 className="text-4xl font-bold">{profile.name}</h2>
          <p className="text-black text-7sm font-semibold">{profile.email}</p>
        </div>
      </div>

      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <input
          type="text"
          placeholder="Search desks or tags"
          className="w-full md:max-w-md p-3 rounded-full border border-gray-300 shadow-sm placeholder:text-[#1E6DB9] text-[#1E6DB9] font-semibold"
        />

        <div className=" overflow-x-scroll whitespace-nowrap mt-3 md:mt-0">
          <div className="flex gap-2">
            {tags.map((tag, idx) => (
              <button
                key={idx}
                className="bg-[#e0e0e0] hover:bg-[#d5d5d5] text-[#1E6DB9] px-4 py-1 rounded-md text-sm font-bold transition whitespace-nowrap"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 md:grid-cols-3 gap-4 mt-8">
        {collections.map((name, idx) => (
          <button
            key={idx}
            className="bg-[#d9d9d9] hover:bg-[#c9c9c9] text-[#1E6DB9] font-bold text-sm py-5 px-4 rounded-lg shadow-sm transition"
          >
            {name}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Profile;