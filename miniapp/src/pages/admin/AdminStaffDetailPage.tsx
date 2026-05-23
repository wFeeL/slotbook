// miniapp/src/pages/admin/AdminStaffDetailPage.tsx
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { useAdminStaff, useArchiveStaff, useReplaceWorkingHours, useStaffWorkingHours, useUpdateStaff } from '@/entities/admin-staff/api';
import { StaffForm, type StaffFormValues } from '@/features/admin-staff/StaffForm';
import { WorkingHoursEditor } from '@/features/admin-staff/WorkingHoursEditor';
import { StaffServicesEditor } from '@/features/admin-staff/StaffServicesEditor';
import { ExceptionsEditor } from '@/features/admin-staff/ExceptionsEditor';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { pushToast } from '@/shared/store/toast-store';
import { cn } from '@/shared/lib/cn';

type Tab = 'profile' | 'services' | 'hours' | 'exceptions';
const TABS: { id: Tab; label: string }[] = [
  { id: 'profile', label: 'Профиль' },
  { id: 'services', label: 'Услуги' },
  { id: 'hours', label: 'Часы' },
  { id: 'exceptions', label: 'Исключения' },
];

export function AdminStaffDetailPage() {
  const params = useParams();
  const navigate = useNavigate();
  const id = Number(params.id);
  const [tab, setTab] = useState<Tab>('profile');

  const staffList = useAdminStaff();
  const staff = (staffList.data ?? []).find((s) => s.id === id);
  const workingHours = useStaffWorkingHours(id, Number.isFinite(id));
  const update = useUpdateStaff();
  const archive = useArchiveStaff();
  const replaceHours = useReplaceWorkingHours();

  if (staffList.isLoading) {
    return <Skeleton height={120} />;
  }
  if (!staff) {
    return <p className="text-sienna-deep">Сотрудник не найден.</p>;
  }

  async function saveProfile(values: StaffFormValues) {
    try {
      const patch: Parameters<typeof update.mutateAsync>[0]['patch'] = {
        name: values.name,
        description: values.description || null,
      };
      if (values.branch_id != null) patch.branch_id = values.branch_id;
      await update.mutateAsync({ id, patch });
      pushToast('success', 'Сохранено');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function archiveStaff() {
    try {
      await archive.mutateAsync(id);
      pushToast('success', 'Сотрудник архивирован');
      navigate('/admin/staff');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function saveHours(entries: Parameters<typeof replaceHours.mutateAsync>[0]['entries']) {
    try {
      await replaceHours.mutateAsync({ id, entries });
      pushToast('success', 'Часы обновлены');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <div className="pt-2 pb-6 flex flex-col gap-4">
      <header className="flex items-center justify-between">
        <h2 className="text-xl text-ink font-display">{staff.name}</h2>
        {!staff.is_active && <Badge tone="clay">Архив</Badge>}
      </header>

      <div className="flex gap-2 overflow-x-auto no-scrollbar -mx-5 px-5">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              'rounded-full px-4 py-1.5 text-sm font-semibold whitespace-nowrap transition',
              tab === t.id ? 'bg-rose text-shell' : 'bg-shell text-sienna-deep border border-sand',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'profile' && (
        <>
          <StaffForm
            initial={{
              name: staff.name,
              description: staff.description ?? '',
              branch_id: staff.branch_id,
            }}
            submitting={update.isPending}
            onSubmit={saveProfile}
          />
          {staff.is_active && (
            <div className="mt-4 pt-4 border-t border-sand">
              <Button variant="ghost" onClick={archiveStaff} disabled={archive.isPending}>
                Архивировать
              </Button>
            </div>
          )}
        </>
      )}

      {tab === 'services' && <StaffServicesEditor staffId={id} />}

      {tab === 'hours' && (
        <WorkingHoursEditor
          initial={workingHours.data ?? []}
          onSave={saveHours}
          saving={replaceHours.isPending}
        />
      )}

      {tab === 'exceptions' && <ExceptionsEditor staffId={id} />}
    </div>
  );
}
