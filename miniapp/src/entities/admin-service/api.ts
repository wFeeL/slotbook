import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { adminServiceKeys } from './model';

export function useAdminServices() {
  return useQuery({
    queryKey: adminServiceKeys.list(),
    queryFn: () => api.services.list(),
    staleTime: 30 * 1000,
  });
}

export function useCreateService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.services.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminServiceKeys.list() });
      // Public client-facing service list shares the same backend resource.
      qc.invalidateQueries({ queryKey: ['services'] });
    },
  });
}

export function useUpdateServiceById() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      patch,
    }: {
      id: number;
      patch: Parameters<typeof api.admin.services.update>[1];
    }) => api.admin.services.update(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminServiceKeys.list() });
      qc.invalidateQueries({ queryKey: ['services'] });
    },
  });
}

export function useArchiveService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.services.archive,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminServiceKeys.list() });
      qc.invalidateQueries({ queryKey: ['services'] });
    },
  });
}
