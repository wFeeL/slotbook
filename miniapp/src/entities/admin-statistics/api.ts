import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import type { StatisticsPeriodT } from '@/shared/api/types';
import { adminStatisticsKeys } from './model';

export function useStatistics(period: StatisticsPeriodT) {
  return useQuery({
    queryKey: adminStatisticsKeys.byPeriod(period),
    queryFn: () => api.admin.statistics(period),
    staleTime: 60 * 1000,
  });
}
