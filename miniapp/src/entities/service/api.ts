import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { serviceKeys } from './model';

export function useServices() {
  return useQuery({
    queryKey: serviceKeys.list(),
    queryFn: () => api.services.list(),
    staleTime: 60 * 1000,
  });
}
