export const adminBookingKeys = {
  list: (filters?: Record<string, unknown>) =>
    filters ? (['admin', 'bookings', filters] as const) : (['admin', 'bookings'] as const),
};
