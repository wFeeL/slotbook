import type { StatisticsPeriodT } from '@/shared/api/types';

export const adminStatisticsKeys = {
  byPeriod: (p: StatisticsPeriodT) => ['admin', 'statistics', p] as const,
};
