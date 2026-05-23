// miniapp/src/features/admin-staff/ExceptionsEditor.tsx
import { useState } from 'react';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Textarea } from '@/shared/ui/Textarea';
import { Sheet } from '@/shared/ui/Sheet';
import { Card } from '@/shared/ui/Card';
import { useCreateException, useDeleteException } from '@/entities/admin-staff/api';
import { pushToast } from '@/shared/store/toast-store';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { request } from '@/shared/api/client';
import { ScheduleExceptionReadSchema, type ScheduleExceptionRead } from '@/shared/api/types';

function useStaffExceptions(staffId: number) {
  return useQuery({
    queryKey: ['admin', 'staff', staffId, 'exceptions'],
    queryFn: () =>
      request(
        `/api/v1/admin/staff/${staffId}/exceptions`,
        { method: 'GET' },
        z.array(ScheduleExceptionReadSchema),
      ),
    staleTime: 30 * 1000,
  });
}

interface ExceptionsEditorProps {
  staffId: number;
}

export function ExceptionsEditor({ staffId }: ExceptionsEditorProps) {
  const list = useStaffExceptions(staffId);
  const createMut = useCreateException();
  const delMut = useDeleteException();
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState('');
  const [type, setType] = useState<'day_off' | 'extra_working_time' | 'blocked_time'>('day_off');
  const [startTime, setStartTime] = useState('10:00');
  const [endTime, setEndTime] = useState('18:00');
  const [reason, setReason] = useState('');

  async function save() {
    if (!date) {
      pushToast('error', 'Укажите дату');
      return;
    }
    try {
      await createMut.mutateAsync({
        staffId,
        body: {
          date,
          type,
          start_time: type !== 'day_off' ? `${startTime}:00` : null,
          end_time: type !== 'day_off' ? `${endTime}:00` : null,
          reason: reason || null,
        },
      });
      pushToast('success', 'Добавлено');
      setOpen(false);
      setDate('');
      setReason('');
      list.refetch();
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function remove(id: number) {
    try {
      await delMut.mutateAsync({ staffId, exceptionId: id });
      pushToast('success', 'Удалено');
      list.refetch();
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-2">
        {(list.data ?? []).length === 0 && (
          <p className="text-sienna-deep text-sm">Нет исключений.</p>
        )}
        {(list.data ?? []).map((ex: ScheduleExceptionRead) => (
          <Card key={ex.id} surface="shell">
            <div className="flex items-center justify-between gap-3">
              <div className="flex-1">
                <div className="text-ink font-semibold">
                  {ex.date} · {ex.type === 'day_off' ? 'Выходной' : `${ex.start_time?.slice(0, 5)}–${ex.end_time?.slice(0, 5)}`}
                </div>
                {ex.reason && <div className="text-sienna-deep text-sm">{ex.reason}</div>}
              </div>
              <Button variant="ghost" onClick={() => remove(ex.id)}>
                Удалить
              </Button>
            </div>
          </Card>
        ))}
      </div>
      <Button onClick={() => setOpen(true)}>+ Добавить исключение</Button>

      <Sheet open={open} onClose={() => setOpen(false)} title="Новое исключение">
        <div className="flex flex-col gap-3">
          <Input
            label="Дата"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
          <Select
            label="Тип"
            value={type}
            onChange={(e) => setType(e.target.value as 'day_off' | 'extra_working_time' | 'blocked_time')}
          >
            <option value="day_off">Выходной</option>
            <option value="extra_working_time">Доп. рабочее время</option>
            <option value="blocked_time">Перерыв</option>
          </Select>
          {type !== 'day_off' && (
            <div className="flex gap-2">
              <Input
                label="С"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
              <Input
                label="По"
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </div>
          )}
          <Textarea
            label="Причина (необязательно)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <div className="flex gap-2">
            <Button onClick={save} disabled={createMut.isPending}>
              Сохранить
            </Button>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Отмена
            </Button>
          </div>
        </div>
      </Sheet>
    </div>
  );
}
