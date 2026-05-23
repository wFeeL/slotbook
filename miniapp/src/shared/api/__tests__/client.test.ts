import { describe, expect, it, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/msw/server';
import { api } from '../endpoints';
import { ApiError, setAuthToken } from '../client';

describe('api client', () => {
  beforeEach(() => setAuthToken(null));

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
});
