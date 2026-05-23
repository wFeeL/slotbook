import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { staffKeys } from './model';

export function useStaffForService(serviceId: number | null) {
  return useQuery({
    queryKey: serviceId ? staffKeys.forService(serviceId) : ['staff', 'disabled'],
    queryFn: () => api.staff.listForService(serviceId!),
    enabled: serviceId !== null,
    staleTime: 60 * 1000,
  });
}
