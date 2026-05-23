import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { adminBusinessKeys } from './model';

export function useAdminBusiness() {
  return useQuery({
    queryKey: adminBusinessKeys.root(),
    queryFn: () => api.admin.business.get(),
    staleTime: 60 * 1000,
  });
}

export function useUpdateBusiness() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.business.update,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminBusinessKeys.root() });
      qc.invalidateQueries({ queryKey: ['slots'] });
    },
  });
}
