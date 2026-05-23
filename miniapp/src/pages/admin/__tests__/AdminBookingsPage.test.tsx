// miniapp/src/pages/admin/__tests__/AdminBookingsPage.test.tsx
import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from '@/test/msw/server';
import { AdminBookingsPage } from '../AdminBookingsPage';

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AdminBookingsPage', () => {
  beforeEach(() => {
    server.use(
      http.get('http://localhost:8000/api/v1/admin/bookings', ({ request }) => {
        const url = new URL(request.url);
        const date = url.searchParams.get('date');
        if (date) {
          return HttpResponse.json([
            {
              id: 100,
              branch_id: 1,
              client_id: 1,
              service_id: 1,
              staff_id: 1,
              starts_at: `${date}T10:00:00Z`,
              ends_at: `${date}T11:00:00Z`,
              status: 'confirmed',
              client_comment: null,
              admin_comment: null,
            },
          ]);
        }
        return HttpResponse.json([]);
      }),
    );
  });

  it('renders bookings for today by default', async () => {
    render(wrap(<AdminBookingsPage />));
    await waitFor(() => expect(screen.getByText(/Услуга #1/)).toBeInTheDocument());
  });
});
