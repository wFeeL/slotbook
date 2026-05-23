import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post('http://localhost:8000/api/v1/auth/telegram', () => {
    return HttpResponse.json({
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 86400,
      user: {
        id: 1,
        telegram_id: 12345,
        first_name: 'Тест',
        last_name: null,
        username: null,
        role: 'client',
      },
    });
  }),
  http.get('http://localhost:8000/api/v1/services', () => {
    return HttpResponse.json([
      {
        id: 1,
        title: 'Массаж спины',
        description: null,
        duration_minutes: 60,
        price: '2500.00',
        is_active: true,
        sort_order: 0,
      },
    ]);
  }),
];
