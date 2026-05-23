import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { adminBookingKeys } from './model';
import { adminDashboardKeys } from '@/entities/admin-dashboard/model';

export function useAdminBookings(filters: Parameters<typeof api.admin.bookings.list>[0]) {
  return useQuery({
    queryKey: adminBookingKeys.list(filters as Record<string, unknown>),
    queryFn: () => api.admin.bookings.list(filters),
    staleTime: 10 * 1000,
  });
}

export function usePatchBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Parameters<typeof api.admin.bookings.patch>[1] }) =>
      api.admin.bookings.patch(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'bookings'] });
      qc.invalidateQueries({ queryKey: ['admin', 'booking'] });
      qc.invalidateQueries({ queryKey: adminDashboardKeys.root() });
    },
  });
}

export function useCreateAdminBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.bookings.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'bookings'] });
      qc.invalidateQueries({ queryKey: ['admin', 'booking'] });
      qc.invalidateQueries({ queryKey: adminDashboardKeys.root() });
      // Admin booking creation consumes a slot — drop public slot cache.
      qc.invalidateQueries({ queryKey: ['slots'] });
    },
  });
}

export function useAdminCancelBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.bookings.cancel,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'bookings'] });
      qc.invalidateQueries({ queryKey: ['admin', 'booking'] });
      qc.invalidateQueries({ queryKey: adminDashboardKeys.root() });
      // Admin cancellation frees a slot — drop public slot cache.
      qc.invalidateQueries({ queryKey: ['slots'] });
    },
  });
}

export function useAdminRescheduleBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, startsAt }: { id: number; startsAt: string }) =>
      api.admin.bookings.reschedule(id, startsAt),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'bookings'] });
      qc.invalidateQueries({ queryKey: ['admin', 'booking'] });
      qc.invalidateQueries({ queryKey: adminDashboardKeys.root() });
      qc.invalidateQueries({ queryKey: ['slots'] });
    },
  });
}
