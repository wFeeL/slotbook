import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import type { WorkingHoursEntry } from '@/shared/api/types';

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

export function useMyWorkingHours() {
  return useQuery({
    queryKey: [...KEY, 'working-hours'],
    queryFn: () => api.staffMe.getWorkingHours(),
  });
}

export function useReplaceMyWorkingHours() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (entries: WorkingHoursEntry[]) =>
      api.staffMe.replaceWorkingHours(entries),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [...KEY, 'working-hours'] });
      qc.invalidateQueries({ queryKey: [...KEY, 'schedule'] });
    },
  });
}

export function useCreateMyException() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      date: string;
      type: 'day_off' | 'extra_working_time' | 'blocked_time';
      start_time?: string | null;
      end_time?: string | null;
      reason?: string | null;
    }) => api.staffMe.createException(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [...KEY, 'schedule'] });
    },
  });
}

export function useDeleteMyException() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.staffMe.deleteException(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [...KEY, 'schedule'] });
    },
  });
}

export function useCancelMyBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.staffMe.cancelBooking(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [...KEY, 'bookings'] });
      qc.invalidateQueries({ queryKey: [...KEY, 'schedule'] });
    },
  });
}

export function useRescheduleMyBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { id: number; starts_at: string }) =>
      api.staffMe.rescheduleBooking(args.id, args.starts_at),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [...KEY, 'bookings'] });
      qc.invalidateQueries({ queryKey: [...KEY, 'schedule'] });
    },
  });
}
