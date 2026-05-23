export const adminBranchKeys = {
  all: () => ['admin', 'branches'] as const,
  list: () => [...adminBranchKeys.all(), 'list'] as const,
};
