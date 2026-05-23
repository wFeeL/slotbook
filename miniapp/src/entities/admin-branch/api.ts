import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { adminBranchKeys } from './model';
import { branchKeys } from '@/entities/branch/model';

export function useAdminBranches() {
  return useQuery({
    queryKey: adminBranchKeys.list(),
    queryFn: () => api.admin.branches.list(),
    staleTime: 30 * 1000,
  });
}

export function useCreateBranch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.branches.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminBranchKeys.list() });
      qc.invalidateQueries({ queryKey: branchKeys.list() });
    },
  });
}

export function useUpdateBranch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      patch,
    }: {
      id: number;
      patch: Parameters<typeof api.admin.branches.update>[1];
    }) => api.admin.branches.update(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminBranchKeys.list() });
      qc.invalidateQueries({ queryKey: branchKeys.list() });
    },
  });
}

export function useArchiveBranch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.admin.branches.archive(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminBranchKeys.list() });
      qc.invalidateQueries({ queryKey: branchKeys.list() });
    },
  });
}
