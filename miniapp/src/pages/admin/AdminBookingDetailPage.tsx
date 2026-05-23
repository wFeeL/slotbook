// miniapp/src/pages/admin/AdminBookingDetailPage.tsx
import { useNavigate, useParams } from 'react-router';
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Textarea } from '@/shared/ui/Textarea';
import { useAdminCancelBooking, usePatchBooking } from '@/entities/admin-booking/api';
import { pushToast } from '@/shared/store/toast-store';
import { showConfirm } from '@/shared/telegram/hooks';
import { request } from '@/shared/api/client';
import { AdminBookingReadSchema, type AdminBookingRead } from '@/shared/api/types';

function useAdminBookingDetail(id: number) {
  return useQuery({
    queryKey: ['admin', 'booking', id],
    queryFn: () =>
      // The backend doesn't have a GET /admin/bookings/{id}; we list and find,
      // but for robustness fetch a list filtered minimally and pick by id.
      request(
        `/api/v1/admin/bookings?limit=200`,
        { method: 'GET' },
        z.array(AdminBookingReadSchema),
      ).then((all: AdminBookingRead[]) => all.find((b) => b.id === id) ?? null),
    staleTime: 5 * 1000,
  });
}

export function AdminBookingDetailPage() {
  const params = useParams();
  const navigate = useNavigate();
  const id = Number(params.id);
  const detail = useAdminBookingDetail(id);
  const patch = usePatchBooking();
  const cancel = useAdminCancelBooking();
  const [adminComment, setAdminComment] = useState('');

  useEffect(() => {
    if (detail.data) setAdminComment(detail.data.admin_comment ?? '');
  }, [detail.data]);

  if (detail.isLoading) return <Skeleton height={160} />;
  if (!detail.data) return <p className="text-sienna">Запись не найдена.</p>;
  const b = detail.data;

  async function setStatus(status: 'completed' | 'no_show') {
    try {
      await patch.mutateAsync({ id, patch: { status } });
      pushToast('success', 'Статус обновлён');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function saveComment() {
    try {
      await patch.mutateAsync({ id, patch: { admin_comment: adminComment || null } });
      pushToast('success', 'Комментарий сохранён');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function cancelBooking() {
    const ok = await showConfirm('Отменить запись?');
    if (!ok) return;
    try {
      await cancel.mutateAsync(id);
      pushToast('success', 'Запись отменена');
      navigate('/admin/bookings');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  const active = b.status === 'pending' || b.status === 'confirmed';

  return (
    <div className="pt-2 pb-6 flex flex-col gap-4">
      <Card surface="shell">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-ink font-semibold text-lg">
              {new Date(b.starts_at).toLocaleString('ru-RU', {
                day: '2-digit',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
            <div className="text-sienna text-sm mt-1">
              Услуга #{b.service_id} · Сотрудник #{b.staff_id} · Клиент #{b.client_id}
            </div>
            {b.client_comment && (
              <div className="text-ink text-sm mt-2 italic">«{b.client_comment}»</div>
            )}
          </div>
          <Badge tone="sage">{b.status}</Badge>
        </div>
      </Card>

      <div>
        <Textarea
          label="Комментарий администратора"
          value={adminComment}
          onChange={(e) => setAdminComment(e.target.value)}
        />
        <Button className="mt-2" variant="secondary" onClick={saveComment} disabled={patch.isPending}>
          Сохранить комментарий
        </Button>
      </div>

      {active && (
        <div className="flex flex-col gap-2 pt-2 border-t border-sand">
          <Button onClick={() => setStatus('completed')} disabled={patch.isPending}>
            Завершено
          </Button>
          <Button variant="secondary" onClick={() => setStatus('no_show')} disabled={patch.isPending}>
            Не пришёл
          </Button>
          <Button variant="ghost" onClick={cancelBooking} disabled={cancel.isPending}>
            Отменить запись
          </Button>
        </div>
      )}
    </div>
  );
}
