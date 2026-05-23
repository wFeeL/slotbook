import { z } from 'zod';
import { ErrorDetailSchema } from './types';

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public extra?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

let currentToken: string | null = null;
let reAuthHandler: (() => Promise<string | null>) | null = null;

export function setAuthToken(token: string | null): void {
  currentToken = token;
}

export function getAuthToken(): string | null {
  return currentToken;
}

export function setReAuthHandler(fn: () => Promise<string | null>): void {
  reAuthHandler = fn;
}

export async function request<T>(
  path: string,
  init: RequestInit | undefined,
  schema: z.ZodType<T>,
): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');
  if (currentToken) headers.set('Authorization', `Bearer ${currentToken}`);

  let response = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (response.status === 401 && reAuthHandler) {
    const newToken = await reAuthHandler();
    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`);
      response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
    }
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const parsed = ErrorDetailSchema.safeParse(body?.detail);
    if (parsed.success) {
      throw new ApiError(response.status, parsed.data.code, parsed.data.message, parsed.data.extra);
    }
    throw new ApiError(response.status, 'unknown', response.statusText);
  }

  return schema.parse(body);
}
