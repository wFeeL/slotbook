import { describe, expect, it } from 'vitest';
import { formatDuration, formatPrice, formatLocalTime } from '../date';

describe('date helpers', () => {
  it('formats short duration', () => {
    expect(formatDuration(30)).toBe('30 мин');
    expect(formatDuration(60)).toBe('1 ч');
    expect(formatDuration(90)).toBe('1 ч 30 мин');
  });

  it('formats price as integer rubles', () => {
    expect(formatPrice('1500.00')).toBe('1500 ₽');
    expect(formatPrice(null)).toBe('');
  });

  it('formats local time from ISO UTC', () => {
    // Note: this runs in JSDOM which uses the test runner's local TZ.
    // We check format only, not exact value.
    const result = formatLocalTime('2026-06-15T07:00:00Z');
    expect(result).toMatch(/^\d{2}:\d{2}$/);
  });
});
