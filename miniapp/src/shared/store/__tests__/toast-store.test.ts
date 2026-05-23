import { describe, expect, it, beforeEach } from 'vitest';
import { useToastStore } from '../toast-store';

describe('toast-store', () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] });
  });

  it('adds a toast with an auto-generated id', () => {
    useToastStore.getState().push({ tone: 'success', message: 'Saved' });
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].message).toBe('Saved');
    expect(toasts[0].tone).toBe('success');
    expect(typeof toasts[0].id).toBe('string');
  });

  it('removes a toast by id', () => {
    useToastStore.getState().push({ tone: 'error', message: 'Boom' });
    const id = useToastStore.getState().toasts[0].id;
    useToastStore.getState().dismiss(id);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });
});
