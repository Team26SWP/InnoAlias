import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JoinGamePage from '../../src/components/JoinGame';

describe('JoinGame', () => {
  it('should render correctly', () => {
    render(<JoinGamePage />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
  it('should not allow code longer than 6 symbols', async () => {
    render(<JoinGamePage />);

    const user = userEvent.setup();
    const code = screen.getByRole('textbox');
    await user.click(code);
    await user.keyboard('ABCDEFG');
    expect(code).toHaveValue('ABCDEF');
  });
});
