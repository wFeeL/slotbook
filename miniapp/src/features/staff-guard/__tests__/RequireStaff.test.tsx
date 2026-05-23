import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { RequireStaff } from '../RequireStaff';
import { useAuthStore } from '@/shared/store/auth-store';
import { useToastStore } from '@/shared/store/toast-store';

function setUser() {
  useAuthStore.setState({
    token: 't',
    user: {
      id: 1,
      telegram_id: 1,
      first_name: null,
      last_name: null,
      username: null,
      role: 'staff',
    },
    staffMe: null,
  });
}

function Harness() {
  return (
    <MemoryRouter initialEntries={['/me']}>
      <Routes>
        <Route path="/" element={<div>home</div>} />
        <Route
          path="/me"
          element={
            <RequireStaff>
              <div>cabinet</div>
            </RequireStaff>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

describe('RequireStaff', () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null, staffMe: null });
    useToastStore.setState({ toasts: [] });
  });

  it('renders nothing while staffMe is loading', () => {
    setUser();
    const { container } = render(<Harness />);
    expect(container.textContent).toBe('');
  });

  it('redirects to / when not linked', () => {
    setUser();
    useAuthStore.setState({
      staffMe: {
        linked: false,
        staff: null,
        branch: null,
        business_timezone: 'UTC',
      },
    });
    render(<Harness />);
    expect(screen.getByText('home')).toBeInTheDocument();
    expect(useToastStore.getState().toasts).toHaveLength(1);
    expect(useToastStore.getState().toasts[0].tone).toBe('error');
  });

  it('renders children when linked', () => {
    setUser();
    useAuthStore.setState({
      staffMe: {
        linked: true,
        staff: { id: 7, branch_id: 1, name: 'A', description: null, is_active: true },
        branch: { id: 1, name: 'Main', timezone: 'UTC' },
        business_timezone: 'UTC',
      },
    });
    render(<Harness />);
    expect(screen.getByText('cabinet')).toBeInTheDocument();
  });
});
