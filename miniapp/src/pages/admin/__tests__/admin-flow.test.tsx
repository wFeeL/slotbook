// miniapp/src/pages/admin/__tests__/admin-flow.test.tsx
import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { App } from '@/app';
import { server } from '@/test/msw/server';
import { setAuthToken } from '@/shared/api/client';
import { useAuthStore } from '@/shared/store/auth-store';

describe('admin flow', () => {
  beforeEach(() => {
    setAuthToken('admin-token');
    useAuthStore.setState({
      token: 'admin-token',
      user: {
        id: 99,
        telegram_id: 99,
        first_name: 'Босс',
        last_name: null,
        username: null,
        role: 'admin',
      },
    });

    server.use(
      http.get('http://localhost:8000/api/v1/admin/dashboard', () =>
        HttpResponse.json({ counts: { today: 3, this_week: 12, no_show_30d: 1 } }),
      ),
      http.get('http://localhost:8000/api/v1/admin/bookings', () => HttpResponse.json([])),
      http.get('http://localhost:8000/api/v1/services', () =>
        HttpResponse.json([
          {
            id: 1,
            title: 'Стрижка',
            description: null,
            duration_minutes: 60,
            price: '1500.00',
            is_active: true,
            sort_order: 0,
          },
        ]),
      ),
    );
  });

  it('admin sees CTA on onboarding and reaches dashboard', async () => {
    window.history.pushState({}, '', '/');
    render(<App />);

    const adminCta = await screen.findByText(/Панель администратора/, {}, { timeout: 5000 });
    await userEvent.click(adminCta);

    await waitFor(
      () => {
        expect(screen.getByText('Сегодня')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      },
      { timeout: 5000 },
    );
  }, 15000);

  it('non-admin is redirected from /admin', async () => {
    useAuthStore.setState({
      token: 'client-token',
      user: {
        id: 1,
        telegram_id: 1,
        first_name: null,
        last_name: null,
        username: null,
        role: 'client',
      },
    });
    window.history.pushState({}, '', '/admin');
    render(<App />);

    await waitFor(
      () => {
        // Onboarding header is "Привет, ..."
        expect(screen.getByText(/Привет,/)).toBeInTheDocument();
      },
      { timeout: 5000 },
    );
  }, 15000);
});
