import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { slotKeys } from './model';

export function useSlotsForDay(args: {
  serviceId: number | null;
  staffId: number | null;
  date: string | null;
}) {
  const enabled = args.serviceId !== null && args.staffId !== null && args.date !== null;
  return useQuery({
    queryKey: enabled
      ? slotKeys.forDay(args.serviceId!, args.staffId!, args.date!)
      : ['slots', 'disabled'],
    queryFn: () =>
      api.slots.forDay({
        serviceId: args.serviceId!,
        staffId: args.staffId!,
        date: args.date!,
      }),
    enabled,
    staleTime: 15 * 1000,
  });
}
