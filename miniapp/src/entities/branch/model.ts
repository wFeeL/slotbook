export const branchKeys = {
  all: () => ['branches'] as const,
  list: () => [...branchKeys.all(), 'list'] as const,
};
