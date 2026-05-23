export const adminStaffKeys = {
  list: () => ['admin', 'staff'] as const,
  detail: (id: number) => ['admin', 'staff', id] as const,
  workingHours: (id: number) => ['admin', 'staff', id, 'working-hours'] as const,
};
