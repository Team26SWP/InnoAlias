import { render, screen } from '@testing-library/react';
import userEvent, { UserEvent } from '@testing-library/user-event';
import CreateGamePage from '../../src/components/CreateGame';

async function enterWord(
  field: HTMLElement,
  submitBtn: HTMLElement,
  text: string,
  user: UserEvent,
) {
  await user.click(field);
  await user.keyboard(text);
  await user.click(submitBtn);
}

describe('CreateGame', () => {
  it('should display a word after it was entered (case-sensitive without leading/trailing spaces)', async () => {
    render(<CreateGamePage aiGame={false} />);

    const inputField = screen.getByRole('textbox');
    const submitButton = screen.getByText('Add');
    const user = userEvent.setup();

    await enterWord(inputField, submitButton, ' hello ', user);
    const addedWord = screen.queryByText('hello');
    expect(addedWord).toBeInTheDocument();
    expect(addedWord).toHaveTextContent('hello');
    expect(inputField).toHaveValue('');

    await enterWord(inputField, submitButton, ' HelLoO ', user);
    const addedWord2 = screen.queryByText('HelLoO');
    expect(addedWord2).toBeInTheDocument();
    expect(addedWord2).toHaveTextContent('HelLoO');
    expect(inputField).toHaveValue('');
  });
});
