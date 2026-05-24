import { useEffect, useState } from 'react';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Button } from '@/shared/ui/Button';
import { Skeleton } from '@/shared/ui/Skeleton';
import { useAdminBusiness, useUpdateBusiness } from '@/entities/admin-business/api';
import { pushToast } from '@/shared/store/toast-store';
import { ApiError } from '@/shared/api/client';

const TIMEZONES = [
  'Europe/Moscow',
  'Europe/Kaliningrad',
  'Europe/Samara',
  'Asia/Yekaterinburg',
  'Asia/Omsk',
  'Asia/Krasnoyarsk',
  'Asia/Irkutsk',
  'Asia/Yakutsk',
  'Asia/Vladivostok',
  'Asia/Magadan',
  'Asia/Kamchatka',
  'UTC',
  'Europe/London',
  'Europe/Berlin',
  'America/New_York',
];

const SLOT_STEPS = [5, 10, 15, 20, 30, 60];

interface BusinessForm {
  name: string;
  timezone: string;
  slot_step_minutes: number;
  booking_buffer_minutes: number;
  min_cancellation_hours: number;
  reminder_long_hours: number;
  reminder_short_hours: number;
}

export function AdminSettingsPage() {
  const q = useAdminBusiness();
  const update = useUpdateBusiness();
  const [form, setForm] = useState<BusinessForm | null>(null);

  useEffect(() => {
    if (q.data) {
      setForm({
        name: q.data.name,
        timezone: q.data.timezone,
        slot_step_minutes: q.data.slot_step_minutes,
        booking_buffer_minutes: q.data.booking_buffer_minutes,
        min_cancellation_hours: q.data.min_cancellation_hours,
        reminder_long_hours: q.data.reminder_long_hours,
        reminder_short_hours: q.data.reminder_short_hours,
      });
    }
  }, [q.data]);

  if (q.isLoading || !form) return <Skeleton height={300} />;

  async function save() {
    if (!form) return;
    try {
      await update.mutateAsync(form);
      pushToast('success', 'Настройки сохранены');
    } catch (e) {
      if (e instanceof ApiError) pushToast('error', e.message);
      else pushToast('error', 'Не удалось сохранить');
    }
  }

  return (
    <div className="pt-2 pb-6 flex flex-col gap-4">
      <h2 className="text-xl text-ink font-display">Настройки бизнеса</h2>

      <Input
        label="Название"
        value={form.name}
        onChange={(e) => setForm({ ...form, name: e.target.value })}
      />

      <Select
        label="Часовой пояс"
        value={form.timezone}
        onChange={(e) => setForm({ ...form, timezone: e.target.value })}
      >
        {TIMEZONES.map((tz) => (
          <option key={tz} value={tz}>
            {tz}
          </option>
        ))}
      </Select>

      <Select
        label="Шаг слотов, мин"
        value={String(form.slot_step_minutes)}
        onChange={(e) => setForm({ ...form, slot_step_minutes: Number(e.target.value) })}
      >
        {SLOT_STEPS.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </Select>

      <Input
        label="Буфер между записями, мин"
        type="number"
        min={0}
        max={60}
        value={String(form.booking_buffer_minutes)}
        onChange={(e) => setForm({ ...form, booking_buffer_minutes: Number(e.target.value) })}
      />

      <Input
        label="Минимум часов до отмены клиентом"
        type="number"
        min={0}
        max={168}
        value={String(form.min_cancellation_hours)}
        onChange={(e) => setForm({ ...form, min_cancellation_hours: Number(e.target.value) })}
      />

      <section className="flex flex-col gap-2 pt-2">
        <h3 className="text-sienna-deep text-xs uppercase tracking-wide">
          Напоминания клиенту о записи
        </h3>
        <p className="text-sienna-deep text-sm">
          Бот шлёт клиенту два напоминания: «длинное» и «короткое». Клиент может
          выключить напоминания в своём профиле.
        </p>
        <Input
          label="За сколько часов до записи — длинное напоминание"
          type="number"
          min={1}
          max={168}
          value={String(form.reminder_long_hours)}
          onChange={(e) =>
            setForm({ ...form, reminder_long_hours: Number(e.target.value) })
          }
        />
        <Input
          label="За сколько часов до записи — короткое напоминание"
          type="number"
          min={0}
          max={24}
          value={String(form.reminder_short_hours)}
          onChange={(e) =>
            setForm({ ...form, reminder_short_hours: Number(e.target.value) })
          }
        />
      </section>

      <Button onClick={save} disabled={update.isPending}>
        {update.isPending ? '...' : 'Сохранить'}
      </Button>
    </div>
  );
}
