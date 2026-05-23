import { useCancelBooking } from '@/entities/booking/api';
import { showConfirm, useHaptic } from '@/shared/telegram/hooks';

export function useCancelWithConfirm() {
  const cancelMutation = useCancelBooking();
  const haptic = useHaptic();

  async function execute(bookingId: number): Promise<boolean> {
    const confirmed = await showConfirm('Точно отменить запись?');
    if (!confirmed) return false;
    try {
      await cancelMutation.mutateAsync(bookingId);
      haptic.success();
      return true;
    } catch {
      haptic.error();
      return false;
    }
  }

  return {
    execute,
    isPending: cancelMutation.isPending,
    error: cancelMutation.error,
  };
}
