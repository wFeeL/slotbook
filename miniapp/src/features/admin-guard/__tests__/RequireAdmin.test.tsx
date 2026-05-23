// miniapp/src/features/admin-guard/__tests__/RequireAdmin.test.tsx
import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { RequireAdmin } from '../RequireAdmin';
import { useAuthStore } from '@/shared/store/auth-store';
import { useToastStore } from '@/shared/store/toast-store';

function setUser(role: 'client' | 'admin' | 'superadmin') {
  useAuthStore.setState({
    token: 't',
    user: {
      id: 1,
      telegram_id: 1,
      first_name: null,
      last_name: null,
      username: null,
      role,
    },
  });
}

describe('RequireAdmin', () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null });
    useToastStore.setState({ toasts: [] });
  });

  it('renders children when role is admin', () => {
    setUser('admin');
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/admin" element={<RequireAdmin><div>inside</div></RequireAdmin>} />
          <Route path="/" element={<div>home</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText('inside')).toBeInTheDocument();
  });

  it('renders children when role is superadmin', () => {
    setUser('superadmin');
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/admin" element={<RequireAdmin><div>inside</div></RequireAdmin>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText('inside')).toBeInTheDocument();
  });

  it('redirects to / and pushes toast for non-admin', () => {
    setUser('client');
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/admin" element={<RequireAdmin><div>inside</div></RequireAdmin>} />
          <Route path="/" element={<div>home</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.queryByText('inside')).not.toBeInTheDocument();
    expect(screen.getByText('home')).toBeInTheDocument();
    expect(useToastStore.getState().toasts).toHaveLength(1);
  });
});
