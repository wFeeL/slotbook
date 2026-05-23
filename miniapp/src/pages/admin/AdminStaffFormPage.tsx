// miniapp/src/pages/admin/AdminStaffFormPage.tsx
import { useNavigate } from 'react-router';
import { StaffForm, type StaffFormValues } from '@/features/admin-staff/StaffForm';
import { useCreateStaff } from '@/entities/admin-staff/api';
import { pushToast } from '@/shared/store/toast-store';
import { useHaptic } from '@/shared/telegram/hooks';

export function AdminStaffFormPage() {
  const navigate = useNavigate();
  const haptic = useHaptic();
  const create = useCreateStaff();

  async function handleSubmit(values: StaffFormValues) {
    try {
      const staff = await create.mutateAsync({
        name: values.name,
        description: values.description || null,
      });
      pushToast('success', 'Сотрудник добавлен');
      haptic.success();
      navigate(`/admin/staff/${staff.id}`);
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
      haptic.error();
    }
  }

  return (
    <div className="pt-2 pb-6">
      <h2 className="text-xl text-ink font-display mb-4">Новый сотрудник</h2>
      <StaffForm
        submitting={create.isPending}
        onSubmit={handleSubmit}
        onCancel={() => navigate('/admin/staff')}
      />
    </div>
  );
}
