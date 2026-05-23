import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { serviceKeys } from './model';

export function useServices(opts: { branchId?: number | null } = {}) {
  const branchId = opts.branchId ?? undefined;
  return useQuery({
    queryKey: [...serviceKeys.list(), branchId ?? 'all'],
    queryFn: () => api.services.list(branchId !== undefined ? { branchId } : {}),
    staleTime: 60 * 1000,
  });
}
