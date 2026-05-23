import { useState } from 'react';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Sheet } from '@/shared/ui/Sheet';
import { Textarea } from '@/shared/ui/Textarea';
import { useCreateMyException, useDeleteMyException } from '@/entities/staff-me/api';
import { pushToast } from '@/shared/store/toast-store';
import type { StaffScheduleDay } from '@/entities/staff-me/model';

type ExceptionType = 'day_off' | 'extra_working_time' | 'blocked_time';

const EXC_LABEL: Record<ExceptionType, string> = {
  day_off: 'Выходной',
  extra_working_time: 'Доп. рабочее время',
  blocked_time: 'Перерыв',
};

interface Props {
  days: StaffScheduleDay[];
}

export function StaffExceptionsEditor({ days }: Props) {
  const create = useCreateMyException();
  const del = useDeleteMyException();
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState('');
  const [type, setType] = useState<ExceptionType>('day_off');
  const [startTime, setStartTime] = useState('10:00');
  const [endTime, setEndTime] = useState('18:00');
  const [reason, setReason] = useState('');

  const allExceptions = days.flatMap((d) => d.exceptions);

  async function save() {
    if (!date) {
      pushToast('error', 'Укажите дату');
      return;
    }
    try {
      await create.mutateAsync({
        date,
        type,
        start_time: type !== 'day_off' ? `${startTime}:00` : null,
        end_time: type !== 'day_off' ? `${endTime}:00` : null,
        reason: reason || null,
      });
      pushToast('success', 'Добавлено');
      setOpen(false);
      setDate('');
      setReason('');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function remove(id: number) {
    try {
      await del.mutateAsync(id);
      pushToast('success', 'Удалено');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sienna-deep text-xs uppercase tracking-wide pt-2">
        Исключения на этой неделе
      </h3>
      {allExceptions.length === 0 && (
        <p className="text-sienna-deep text-sm">Исключений нет.</p>
      )}
      {allExceptions.map((ex) => (
        <Card key={ex.id} surface="shell">
          <div className="flex items-center justify-between gap-3">
            <div className="flex-1">
              <div className="text-ink font-semibold">
                {ex.date} ·{' '}
                {ex.type === 'day_off'
                  ? EXC_LABEL.day_off
                  : `${ex.start_time?.slice(0, 5)}–${ex.end_time?.slice(0, 5)}`}
              </div>
              {ex.reason && (
                <div className="text-sienna-deep text-sm">{ex.reason}</div>
              )}
            </div>
            <Button variant="ghost" onClick={() => remove(ex.id)}>
              Удалить
            </Button>
          </div>
        </Card>
      ))}
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
            onChange={(e) => setType(e.target.value as ExceptionType)}
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
            <Button onClick={save} disabled={create.isPending}>
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
