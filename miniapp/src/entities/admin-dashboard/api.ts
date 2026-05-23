import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { adminDashboardKeys } from './model';

export function useAdminDashboard() {
  return useQuery({
    queryKey: adminDashboardKeys.root(),
    queryFn: () => api.admin.dashboard(),
    staleTime: 30 * 1000,
  });
}
