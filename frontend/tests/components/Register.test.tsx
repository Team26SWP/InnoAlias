import { render, screen } from '@testing-library/react';
import userEvent, { UserEvent } from '@testing-library/user-event';
import RegisterPage from '../../src/components/Register';

async function enterText(element: HTMLElement, text: string, user: UserEvent) {
  await user.click(element);
  await user.keyboard(text);
}

describe('Register', () => {
  it('should render correctly', () => {
    render(<RegisterPage />);

    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText(/surname/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

    expect(screen.getByText('Create')).toBeInTheDocument();
  });

  it('should deny an incorrect email', async () => {
    render(<RegisterPage />);
    const name = screen.getByLabelText('Name');
    const surname = screen.getByLabelText(/surname/i);
    const email = screen.getByLabelText(/email/i);
    const password = screen.getByLabelText(/password/i);

    const user = userEvent.setup();

    await enterText(name, 'Bob', user);
    await enterText(surname, 'Smith', user);
    await enterText(email, '1234', user);
    await enterText(password, 'password', user);

    await user.click(screen.getByText('Create'));
    expect(email).toBeInvalid();
  });
});
