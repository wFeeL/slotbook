import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { branchKeys } from './model';

export function useBranches() {
  return useQuery({
    queryKey: branchKeys.list(),
    queryFn: () => api.branches.list(),
    staleTime: 60 * 1000,
  });
}
