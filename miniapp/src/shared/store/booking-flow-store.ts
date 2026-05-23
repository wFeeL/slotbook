import { create } from 'zustand';

interface BookingFlowState {
  serviceId: number | null;
  staffId: number | null;
  date: string | null; // YYYY-MM-DD (local business date)
  startsAt: string | null; // ISO 8601 UTC
  comment: string;
  setService(id: number): void;
  setStaff(id: number): void;
  setDate(date: string): void;
  setStartsAt(iso: string): void;
  setComment(c: string): void;
  reset(): void;
}

const initialState = {
  serviceId: null,
  staffId: null,
  date: null,
  startsAt: null,
  comment: '',
};

export const useBookingFlowStore = create<BookingFlowState>((set) => ({
  ...initialState,
  setService(id) {
    // Changing the service invalidates downstream choices
    set({ ...initialState, serviceId: id });
  },
  setStaff(id) {
    set((s) => ({ ...s, staffId: id, date: null, startsAt: null }));
  },
  setDate(date) {
    set((s) => ({ ...s, date, startsAt: null }));
  },
  setStartsAt(iso) {
    set((s) => ({ ...s, startsAt: iso }));
  },
  setComment(comment) {
    set((s) => ({ ...s, comment: comment.slice(0, 1000) }));
  },
  reset() {
    set(initialState);
  },
}));
