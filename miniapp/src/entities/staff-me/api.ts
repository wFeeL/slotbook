import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';

const KEY = ['staff-me'] as const;

export function useStaffMe() {
  return useQuery({
    queryKey: [...KEY, 'profile'],
    queryFn: () => api.staffMe.profile(),
  });
}

export function useMyBookings(
  filters: { date?: string; from?: string; to?: string; status?: string } = {},
) {
  return useQuery({
    queryKey: [...KEY, 'bookings', filters],
    queryFn: () => api.staffMe.bookings(filters),
  });
}

export function useMySchedule(weekStart?: string) {
  return useQuery({
    queryKey: [...KEY, 'schedule', weekStart ?? null],
    queryFn: () => api.staffMe.schedule(weekStart),
  });
}

export function useUpdateMyBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: {
      id: number;
      status?: 'completed' | 'no_show';
      admin_comment?: string | null;
    }) =>
      api.staffMe.patchBooking(args.id, {
        status: args.status,
        admin_comment: args.admin_comment,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [...KEY, 'bookings'] });
      qc.invalidateQueries({ queryKey: [...KEY, 'schedule'] });
    },
  });
}
