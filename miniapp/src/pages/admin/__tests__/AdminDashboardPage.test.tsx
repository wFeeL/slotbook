// miniapp/src/pages/admin/__tests__/AdminDashboardPage.test.tsx
import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from '@/test/msw/server';
import { AdminDashboardPage } from '../AdminDashboardPage';

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AdminDashboardPage', () => {
  beforeEach(() => {
    server.use(
      http.get('http://localhost:8000/api/v1/admin/dashboard', () =>
        HttpResponse.json({ counts: { today: 5, this_week: 17, no_show_30d: 2 } }),
      ),
      http.get('http://localhost:8000/api/v1/admin/bookings', () => HttpResponse.json([])),
    );
  });

  it('renders three counters', async () => {
    render(wrap(<AdminDashboardPage />));
    expect(await screen.findByText('5')).toBeInTheDocument();
    expect(await screen.findByText('17')).toBeInTheDocument();
    expect(await screen.findByText('2')).toBeInTheDocument();
  });
});
