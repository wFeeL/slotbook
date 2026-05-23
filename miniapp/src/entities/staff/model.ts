export const staffKeys = {
  all: () => ['staff'] as const,
  forService: (serviceId: number) => [...staffKeys.all(), 'forService', serviceId] as const,
};
