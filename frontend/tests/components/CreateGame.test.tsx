import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CreateGamePage from '../../src/components/CreateGame';

describe('CreateGame', () => {
  it('should display a word after it was entered (in lowercase without leading/trailing spaces)', async () => {
    render(<CreateGamePage />);

    const inputField = screen.getByRole('textbox');
    const submitButton = screen.getByText('Add');
    const user = userEvent.setup();
    await user.click(inputField);
    await user.keyboard(' Hello ');
    await user.click(submitButton);

    const addedWord = screen.queryByText(/hello/i);
    expect(addedWord).toBeInTheDocument();
    expect(addedWord).toHaveTextContent('hello');
    expect(inputField).toHaveValue('');
  });
});
