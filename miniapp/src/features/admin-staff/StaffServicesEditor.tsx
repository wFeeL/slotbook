// miniapp/src/features/admin-staff/StaffServicesEditor.tsx
import { useEffect, useState } from 'react';
import { Toggle } from '@/shared/ui/Toggle';
import { Button } from '@/shared/ui/Button';
import { Skeleton } from '@/shared/ui/Skeleton';
import { useAdminServices } from '@/entities/admin-service/api';
import { useReplaceStaffServices } from '@/entities/admin-staff/api';
import { pushToast } from '@/shared/store/toast-store';
import { api } from '@/shared/api/endpoints';
import { useQuery } from '@tanstack/react-query';

interface StaffServicesEditorProps {
  staffId: number;
}

function useStaffServiceIds(staffId: number) {
  // The backend doesn't expose a direct "services for staff" admin endpoint;
  // we reverse-derive by listing all services and asking the public staff
  // endpoint per service. If the staff appears, that service is assigned.
  return useQuery({
    queryKey: ['admin', 'staff', staffId, 'service-ids'],
    queryFn: async () => {
      const services = await api.services.list();
      const ids: number[] = [];
      for (const s of services) {
        const list = await api.staff.listForService(s.id);
        if (list.some((m) => m.id === staffId)) ids.push(s.id);
      }
      return ids;
    },
    staleTime: 30 * 1000,
  });
}

export function StaffServicesEditor({ staffId }: StaffServicesEditorProps) {
  const services = useAdminServices();
  const currentIds = useStaffServiceIds(staffId);
  const replace = useReplaceStaffServices();
  const [selected, setSelected] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (currentIds.data) setSelected(new Set(currentIds.data));
  }, [currentIds.data]);

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

  if (services.isLoading || currentIds.isLoading) {
    return <Skeleton height={120} />;
  }

  return (
    <div className="flex flex-col gap-3">
      {(services.data ?? []).map((s) => (
        <div key={s.id} className="flex items-center justify-between rounded-2xl bg-shell border border-sand px-4 py-3">
          <div className="flex-1">
            <div className="text-ink">{s.title}</div>
            <div className="text-sienna text-xs">{s.duration_minutes} мин</div>
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
