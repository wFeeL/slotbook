// miniapp/src/pages/admin/AdminBookingNewPage.tsx
import { useNavigate } from 'react-router';
import { BookingForm, type BookingFormValues } from '@/features/admin-bookings/BookingForm';
import { useCreateAdminBooking } from '@/entities/admin-booking/api';
import { pushToast } from '@/shared/store/toast-store';
import { useHaptic } from '@/shared/telegram/hooks';
import { ApiError } from '@/shared/api/client';

export function AdminBookingNewPage() {
  const navigate = useNavigate();
  const create = useCreateAdminBooking();
  const haptic = useHaptic();

  async function handleSubmit(values: BookingFormValues) {
    try {
      const created = await create.mutateAsync({
        client_telegram_id: values.client_telegram_id,
        service_id: values.service_id,
        staff_id: values.staff_id,
        starts_at: values.starts_at,
        client_comment: values.client_comment || null,
        admin_comment: values.admin_comment || null,
      });
      pushToast('success', 'Запись создана');
      haptic.success();
      navigate(`/admin/bookings/${created.id}`);
    } catch (e) {
      haptic.error();
      if (e instanceof ApiError && e.code === 'slot_already_taken') {
        pushToast('error', 'Слот уже занят');
      } else {
        pushToast('error', e instanceof Error ? e.message : 'Не удалось создать');
      }
    }
  }

  return (
    <div className="pt-2 pb-6">
      <h2 className="text-xl text-ink font-display mb-4">Новая запись</h2>
      <BookingForm
        submitting={create.isPending}
        onSubmit={handleSubmit}
        onCancel={() => navigate('/admin/bookings')}
      />
    </div>
  );
}
