export const bookingKeys = {
  all: () => ['bookings'] as const,
  my: () => [...bookingKeys.all(), 'my'] as const,
};
