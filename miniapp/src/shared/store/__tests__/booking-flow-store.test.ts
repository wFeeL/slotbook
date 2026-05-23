import { describe, expect, it, beforeEach } from 'vitest';
import { useBookingFlowStore } from '../booking-flow-store';

describe('booking-flow-store', () => {
  beforeEach(() => {
    useBookingFlowStore.getState().reset();
  });

  it('setService clears downstream choices', () => {
    const s = useBookingFlowStore.getState();
    s.setService(1);
    s.setStaff(2);
    s.setDate('2026-06-15');
    s.setStartsAt('2026-06-15T07:00:00Z');
    s.setService(99);
    const after = useBookingFlowStore.getState();
    expect(after.serviceId).toBe(99);
    expect(after.staffId).toBeNull();
    expect(after.date).toBeNull();
    expect(after.startsAt).toBeNull();
  });

  it('setStaff clears date and startsAt', () => {
    const s = useBookingFlowStore.getState();
    s.setService(1);
    s.setStaff(2);
    s.setDate('2026-06-15');
    s.setStartsAt('2026-06-15T07:00:00Z');
    s.setStaff(3);
    const after = useBookingFlowStore.getState();
    expect(after.staffId).toBe(3);
    expect(after.date).toBeNull();
    expect(after.startsAt).toBeNull();
  });

  it('setComment trims to 1000 chars', () => {
    useBookingFlowStore.getState().setComment('a'.repeat(2000));
    expect(useBookingFlowStore.getState().comment.length).toBe(1000);
  });
});
