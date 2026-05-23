export const slotKeys = {
  all: () => ['slots'] as const,
  forDay: (serviceId: number, staffId: number, date: string) =>
    [...slotKeys.all(), serviceId, staffId, date] as const,
};
