import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from '@/test/msw/server';
import { useAuthStore } from '@/shared/store/auth-store';
import { StaffCabinetPage } from '../StaffCabinetPage';

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('StaffCabinetPage', () => {
  beforeEach(() => {
    useAuthStore.setState({
      token: 't',
      user: {
        id: 1,
        telegram_id: 1,
        first_name: 'Anna',
        last_name: null,
        username: null,
        role: 'staff',
      },
      staffMe: {
        linked: true,
        staff: { id: 7, branch_id: 1, name: 'Anna', description: null, is_active: true },
        branch: { id: 1, name: 'Main', timezone: 'UTC' },
        business_timezone: 'UTC',
      },
    });
    const tomorrowIso = new Date(Date.now() + 3600_000).toISOString();
    const inTwoHoursIso = new Date(Date.now() + 7200_000).toISOString();
    server.use(
      http.get('http://localhost:8000/api/v1/staff/me', () =>
        HttpResponse.json({
          linked: true,
          staff: { id: 7, branch_id: 1, name: 'Anna', description: null, is_active: true },
          branch: { id: 1, name: 'Main', timezone: 'UTC' },
          business_timezone: 'UTC',
        }),
      ),
      http.get('http://localhost:8000/api/v1/staff/me/bookings', () =>
        HttpResponse.json([
          {
            id: 42,
            starts_at: tomorrowIso,
            ends_at: inTwoHoursIso,
            status: 'confirmed',
            service_id: 1,
            service_title: 'Стрижка',
            service_duration_minutes: 30,
            service_price: '1000',
            client_first_name: 'Иван',
            client_last_name: null,
            client_phone: '+71234567890',
            client_username: 'ivan',
            client_comment: null,
            admin_comment: null,
          },
        ]),
      ),
      http.get('http://localhost:8000/api/v1/staff/me/schedule', () =>
        HttpResponse.json({
          week_start: '2026-05-18',
          business_timezone: 'UTC',
          days: [],
        }),
      ),
      http.get('http://localhost:8000/api/v1/staff/me/working-hours', () =>
        HttpResponse.json([]),
      ),
      http.get('http://localhost:8000/api/v1/staff/me/statistics', () =>
        HttpResponse.json({
          period: '30d',
          revenue: '0',
          total_bookings: 0,
          completed_count: 0,
          no_show_count: 0,
          cancellation_count: 0,
          cancellation_rate: 0,
          top_services: [],
          top_staff: [],
          daily_volume: [],
        }),
      ),
    );
  });

  it('renders today booking with action buttons', async () => {
    render(wrap(<StaffCabinetPage />));
    expect(await screen.findByText('Стрижка')).toBeInTheDocument();
    expect(screen.getByText(/Иван/)).toBeInTheDocument();
    expect(screen.getByText('Завершить')).toBeInTheDocument();
    expect(screen.getByText('Не пришёл')).toBeInTheDocument();
    expect(screen.getByText('Перенести')).toBeInTheDocument();
  });
});
