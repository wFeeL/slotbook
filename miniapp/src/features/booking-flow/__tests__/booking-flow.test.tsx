import { describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { App } from '@/app';
import { server } from '@/test/msw/server';
import { setAuthToken } from '@/shared/api/client';
import { useBookingFlowStore } from '@/shared/store/booking-flow-store';

const today = new Date();
const dateStr = today.toISOString().slice(0, 10);

function setupHandlers() {
  server.use(
    http.get('http://localhost:8000/api/v1/staff', () =>
      HttpResponse.json([
        { id: 10, branch_id: 1, name: 'Алексей', description: null, is_active: true },
      ]),
    ),
    http.get('http://localhost:8000/api/v1/slots', () =>
      HttpResponse.json({
        date: dateStr,
        timezone: 'Europe/Moscow',
        slots: [
          {
            starts_at: `${dateStr}T10:00:00Z`,
            ends_at: `${dateStr}T11:00:00Z`,
            starts_at_local: `${dateStr}T13:00:00+03:00`,
            ends_at_local: `${dateStr}T14:00:00+03:00`,
          },
        ],
      }),
    ),
    http.post('http://localhost:8000/api/v1/bookings', () =>
      HttpResponse.json({
        id: 42,
        branch_id: 1,
        service_id: 1,
        staff_id: 10,
        starts_at: `${dateStr}T10:00:00Z`,
        ends_at: `${dateStr}T11:00:00Z`,
        status: 'confirmed',
        client_comment: null,
      }),
    ),
  );
}

describe('booking flow integration', () => {
  it('completes end-to-end and lands on success page', async () => {
    // Reset store state before test
    useBookingFlowStore.getState().reset();

    setupHandlers();
    setAuthToken('dev-token');
    window.history.pushState({}, '', '/book/service');

    render(<App />);

    // Step 1: pick a service (generous timeout to allow Suspense/lazy load to resolve)
    const serviceCard = await screen.findByText(/Массаж спины/, {}, { timeout: 5000 });
    await userEvent.click(serviceCard);

    // Step 2: pick a staff
    const staffCard = await screen.findByText(/Алексей/, {}, { timeout: 5000 });
    await userEvent.click(staffCard);

    // Step 3: pick today (first day chip with a numeric label)
    const dayChips = await screen.findAllByRole('button', { name: /\d+/ }, { timeout: 5000 });
    await userEvent.click(dayChips[0]);

    // Step 4: pick the only slot
    const slotChip = await screen.findByRole('button', { name: /:00/ }, { timeout: 5000 });
    await userEvent.click(slotChip);

    // Step 5: navigate to confirm — use the fallback browser button (Telegram MainButton is absent in tests)
    const nextBtn = await screen.findByRole('button', { name: /Далее/ }, { timeout: 5000 });
    await userEvent.click(nextBtn);

    // Step 6: confirm booking
    const confirmBtn = await screen.findByRole('button', { name: /Подтвердить запись/ }, { timeout: 5000 });
    await userEvent.click(confirmBtn);

    // Wait for navigation to success page (lazy-loaded, so Suspense resolves first)
    await waitFor(() => expect(screen.getByText(/Готово/)).toBeInTheDocument(), { timeout: 10000 });
  }, 20000);
});
