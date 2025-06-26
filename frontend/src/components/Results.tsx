import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

/**
 * Interface defining the structure of a player's score
 * @property id - Unique identifier for the player
 * @property name - Player's display name
 * @property score - Player's final score
 * @property rank - Player's final ranking
 */
interface PlayerScore {
  id: string;
  name: string;
  score: number;
  rank: number;
}

// Mock data for testing the results display
// TODO: Replace with actual API call to fetch real results
const mockResults: PlayerScore[] = [
  { id: '1', name: 'Player 1', score: 8, rank: 1 },
  { id: '2', name: 'Player 2', score: 6, rank: 2 },
  { id: '3', name: 'Player 3', score: 4, rank: 3 },
];

/**
 * Results Component
 * 
 * This component displays the final game results, including:
 * 1. Top 3 players with special highlighting
 * 2. Complete list of all players and their scores
 * 3. Option to play again
 * 
 * Currently uses mock data, but should be updated to fetch real results
 * from the backend when implemented.
 */
const Results: React.FC = () => {
  // Get game ID from URL parameters
  const { gameId } = useParams<{ gameId: string }>();
  // Hook for programmatic navigation
  const navigate = useNavigate();

  /**
   * Handles navigation back to home page when "Play Again" is clicked
   */
  const handlePlayAgain = () => {
    navigate('/');
  };

   return (
    <div className="bg-[#FAF6E9] dark:bg-[#1A1A1A] min-h-screen flex flex-col items-center py-10 px-4 font-[ADLaM_Display]">
      <h1 className="text-2xl sm:text-3xl text-[#3171a6] font-bold mb-6">
        Leaderboard
      </h1>

      <div className="w-full max-w-2xl bg-[#d9d9d9] rounded-xl p-4 flex flex-col gap-2 max-h-[400px] overflow-y-auto">
        {mockResults.map((player) => (
          <div
            key={player.id}
            className="bg-[#bfbfbf] rounded-md px-4 py-2 flex justify-between text-[#3171a6] text-[16px] font-bold"
          >
            <span>{player.rank}.</span>
            <span>{player.name}</span>
            <span>{player.score}</span>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap justify-center gap-4">
        <button className="bg-[#d9d9d9] text-[#3171a6] text-xl px-5 py-2 rounded-lg font-semibold">
          Export Leaderboard
        </button>
        <button
          onClick={() => navigate("/")}
          className="bg-[#3171a6] text-[#fff1e8] text-xl px-5 py-2 rounded-lg font-semibold"
        >
          Back to main
        </button>
        <button className="bg-[#d9d9d9] text-[#3171a6] text-xl px-5 py-2 rounded-lg font-semibold">
          Save Deck
        </button>
      </div>
    </div>
  );
};
export default Results; 