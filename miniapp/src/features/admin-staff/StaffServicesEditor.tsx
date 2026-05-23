// miniapp/src/features/admin-staff/StaffServicesEditor.tsx
import { useEffect, useState } from 'react';
import { Toggle } from '@/shared/ui/Toggle';
import { Button } from '@/shared/ui/Button';
import { Skeleton } from '@/shared/ui/Skeleton';
import { useAdminServices } from '@/entities/admin-service/api';
import { useAdminStaff, useReplaceStaffServices } from '@/entities/admin-staff/api';
import { pushToast } from '@/shared/store/toast-store';

interface StaffServicesEditorProps {
  staffId: number;
}

export function StaffServicesEditor({ staffId }: StaffServicesEditorProps) {
  const services = useAdminServices();
  const staffList = useAdminStaff();
  const currentIds = (staffList.data ?? []).find((s) => s.id === staffId)?.service_ids ?? [];
  const replace = useReplaceStaffServices();
  const [selected, setSelected] = useState<Set<number>>(new Set());

  // Hydrate selected from the staff list once it loads. Track only the
  // identity of the underlying data so we don't re-hydrate on every render.
  useEffect(() => {
    if (staffList.data) {
      setSelected(new Set(currentIds));
    }
    // currentIds is derived from staffList.data; depending on staffList.data is enough.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [staffList.data, staffId]);

  function toggle(id: number) {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function save() {
    try {
      await replace.mutateAsync({ id: staffId, serviceIds: Array.from(selected) });
      pushToast('success', 'Услуги обновлены');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  if (services.isLoading || staffList.isLoading) {
    return <Skeleton height={120} />;
  }

  return (
    <div className="flex flex-col gap-3">
      {(services.data ?? []).map((s) => (
        <div key={s.id} className="flex items-center justify-between rounded-2xl bg-shell border border-sand px-4 py-3">
          <div className="flex-1">
            <div className="text-ink">{s.title}</div>
            <div className="text-sienna-deep text-xs">{s.duration_minutes} мин</div>
          </div>
          <Toggle checked={selected.has(s.id)} onChange={() => toggle(s.id)} />
        </div>
      ))}
      <Button onClick={save} disabled={replace.isPending}>
        {replace.isPending ? '...' : 'Сохранить'}
      </Button>
    </div>
  );
}
