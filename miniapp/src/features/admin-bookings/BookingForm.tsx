// miniapp/src/features/admin-bookings/BookingForm.tsx
import { useState, type FormEvent } from 'react';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Textarea } from '@/shared/ui/Textarea';
import { Button } from '@/shared/ui/Button';
import { useAdminServices } from '@/entities/admin-service/api';
import { useAdminStaff } from '@/entities/admin-staff/api';

export interface BookingFormValues {
  client_telegram_id: number;
  service_id: number;
  staff_id: number;
  starts_at: string; // ISO string
  client_comment: string;
  admin_comment: string;
}

interface BookingFormProps {
  submitting?: boolean;
  onSubmit(values: BookingFormValues): void;
  onCancel?: () => void;
}

export function BookingForm({ submitting, onSubmit, onCancel }: BookingFormProps) {
  const services = useAdminServices();
  const staff = useAdminStaff();

  const [telegramId, setTelegramId] = useState('');
  const [serviceId, setServiceId] = useState('');
  const [staffId, setStaffId] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('10:00');
  const [clientComment, setClientComment] = useState('');
  const [adminComment, setAdminComment] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const errs: Record<string, string> = {};
    const tgIdNum = Number(telegramId);
    if (!telegramId || !Number.isFinite(tgIdNum) || tgIdNum <= 0)
      errs.telegramId = 'Укажите Telegram ID';
    if (!serviceId) errs.serviceId = 'Выберите услугу';
    if (!staffId) errs.staffId = 'Выберите сотрудника';
    if (!date) errs.date = 'Выберите дату';
    if (!time) errs.time = 'Выберите время';
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    // Build an ISO string with the admin's local UTC offset so backend records
    // the intended wall-clock time, not a UTC-shifted one.
    const local = new Date(`${date}T${time}:00`);
    const offsetMin = -local.getTimezoneOffset(); // sign-flipped: + for east of UTC
    const sign = offsetMin >= 0 ? '+' : '-';
    const abs = Math.abs(offsetMin);
    const offHH = String(Math.floor(abs / 60)).padStart(2, '0');
    const offMM = String(abs % 60).padStart(2, '0');
    const startsAt = `${date}T${time}:00${sign}${offHH}:${offMM}`;

    onSubmit({
      client_telegram_id: tgIdNum,
      service_id: Number(serviceId),
      staff_id: Number(staffId),
      starts_at: startsAt,
      client_comment: clientComment,
      admin_comment: adminComment,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Input
        label="Telegram ID клиента"
        type="number"
        value={telegramId}
        onChange={(e) => setTelegramId(e.target.value)}
        error={errors.telegramId ?? null}
        placeholder="123456789"
      />
      <Select
        label="Услуга"
        value={serviceId}
        onChange={(e) => setServiceId(e.target.value)}
        error={errors.serviceId ?? null}
      >
        <option value="">— выберите —</option>
        {(services.data ?? []).map((s) => (
          <option key={s.id} value={s.id}>
            {s.title} · {s.duration_minutes} мин
          </option>
        ))}
      </Select>
      <Select
        label="Сотрудник"
        value={staffId}
        onChange={(e) => setStaffId(e.target.value)}
        error={errors.staffId ?? null}
      >
        <option value="">— выберите —</option>
        {(staff.data ?? []).map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </Select>
      <div className="flex gap-2">
        <Input
          label="Дата"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          error={errors.date ?? null}
        />
        <Input
          label="Время"
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          error={errors.time ?? null}
        />
      </div>
      <Textarea
        label="Комментарий клиента"
        value={clientComment}
        onChange={(e) => setClientComment(e.target.value)}
      />
      <Textarea
        label="Комментарий администратора"
        value={adminComment}
        onChange={(e) => setAdminComment(e.target.value)}
      />
      <div className="flex gap-2 pt-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? '...' : 'Создать запись'}
        </Button>
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Отмена
          </Button>
        )}
      </div>
    </form>
  );
}
