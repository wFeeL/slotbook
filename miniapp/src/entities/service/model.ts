export const serviceKeys = {
  all: () => ['services'] as const,
  list: () => [...serviceKeys.all(), 'list'] as const,
};
