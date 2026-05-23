export const staffKeys = {
  all: () => ['staff'] as const,
  forService: (serviceId: number, branchId?: number | null) =>
    [...staffKeys.all(), 'forService', serviceId, branchId ?? null] as const,
};
