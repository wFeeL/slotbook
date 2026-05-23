import { describe, expect, it, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/msw/server';
import { api } from '../endpoints';
import { ApiError, setAuthToken, setReAuthHandler } from '../client';

describe('api client', () => {
  beforeEach(() => {
    setAuthToken(null);
    setReAuthHandler(null);
  });

  it('parses service list with Zod', async () => {
    const services = await api.services.list();
    expect(services).toHaveLength(1);
    expect(services[0].title).toBe('Массаж спины');
  });

  it('throws ApiError with code on 4xx responses', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/services', () =>
        HttpResponse.json({ detail: { code: 'invalid_token', message: 'no auth' } }, { status: 401 }),
      ),
    );
    await expect(api.services.list()).rejects.toMatchObject({
      status: 401,
      code: 'invalid_token',
    });
    await expect(api.services.list()).rejects.toBeInstanceOf(ApiError);
  });

  it('invokes the re-auth handler on 401 and retries with new token', async () => {
    let callCount = 0;
    server.use(
      http.get('http://localhost:8000/api/v1/services', ({ request: req }) => {
        callCount += 1;
        const auth = req.headers.get('Authorization');
        if (auth === 'Bearer fresh-token') {
          return HttpResponse.json([
            {
              id: 1,
              branch_id: 1,
              title: 'Recovered',
              description: null,
              duration_minutes: 30,
              price: null,
              is_active: true,
              sort_order: 0,
            },
          ]);
        }
        return HttpResponse.json(
          { detail: { code: 'invalid_token', message: 'expired' } },
          { status: 401 },
        );
      }),
    );

    const reAuth = vi.fn(async () => 'fresh-token');
    setReAuthHandler(reAuth);

    const services = await api.services.list();
    expect(reAuth).toHaveBeenCalledTimes(1);
    expect(services[0].title).toBe('Recovered');
    expect(callCount).toBe(2);
  });
});
