import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { staffKeys } from './model';

export function useStaffForService(serviceId: number | null, branchId?: number | null) {
  return useQuery({
    queryKey: serviceId ? staffKeys.forService(serviceId, branchId) : ['staff', 'disabled'],
    queryFn: () =>
      api.staff.listForService(serviceId!, branchId != null ? { branchId } : {}),
    enabled: serviceId !== null,
    staleTime: 60 * 1000,
  });
}
