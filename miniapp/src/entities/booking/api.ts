import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { bookingKeys } from './model';
import { slotKeys } from '../slot/model';

export function useMyBookings() {
  return useQuery({
    queryKey: bookingKeys.my(),
    queryFn: () => api.bookings.listMy(),
    staleTime: 10 * 1000,
  });
}

export function useCreateBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.bookings.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: bookingKeys.my() });
      qc.invalidateQueries({ queryKey: slotKeys.all() });
    },
  });
}

export function useCancelBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.bookings.cancel,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: bookingKeys.my() });
      qc.invalidateQueries({ queryKey: slotKeys.all() });
    },
  });
}
