// miniapp/src/pages/admin/__tests__/AdminServicesPage.test.tsx
import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from '@/test/msw/server';
import { AdminServicesPage } from '../AdminServicesPage';

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AdminServicesPage', () => {
  beforeEach(() => {
    server.use(
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

  it('lists services and shows create CTA', async () => {
    render(wrap(<AdminServicesPage />));
    expect(await screen.findByText('Стрижка')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Добавить/ })).toBeInTheDocument();
  });
});
