import { useState, type FormEvent } from 'react';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Button } from '@/shared/ui/Button';

export interface BranchFormValues {
  name: string;
  address: string;
  timezone: string;
  sort_order: number;
  is_active: boolean;
}

interface BranchFormProps {
  initial?: Partial<BranchFormValues>;
  submitting?: boolean;
  submitLabel?: string;
  showActiveToggle?: boolean;
  onSubmit(values: BranchFormValues): void;
  onCancel?: () => void;
}

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

export function BranchForm({
  initial,
  submitting,
  submitLabel = 'Сохранить',
  showActiveToggle,
  onSubmit,
  onCancel,
}: BranchFormProps) {
  const [values, setValues] = useState<BranchFormValues>({
    name: initial?.name ?? '',
    address: initial?.address ?? '',
    timezone: initial?.timezone ?? 'Europe/Moscow',
    sort_order: initial?.sort_order ?? 0,
    is_active: initial?.is_active ?? true,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof BranchFormValues, string>>>({});

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const errs: typeof errors = {};
    if (!values.name.trim()) errs.name = 'Введите название';
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Input
        label="Название"
        value={values.name}
        onChange={(e) => setValues({ ...values, name: e.target.value })}
        error={errors.name ?? null}
        placeholder="Например, Центр"
      />
      <Input
        label="Адрес"
        value={values.address}
        onChange={(e) => setValues({ ...values, address: e.target.value })}
        placeholder="ул. Ленина, 1"
      />
      <Select
        label="Часовой пояс"
        value={values.timezone}
        onChange={(e) => setValues({ ...values, timezone: e.target.value })}
      >
        {TIMEZONES.map((tz) => (
          <option key={tz} value={tz}>
            {tz}
          </option>
        ))}
      </Select>
      <Input
        label="Порядок"
        type="number"
        value={String(values.sort_order)}
        onChange={(e) => setValues({ ...values, sort_order: Number(e.target.value) })}
      />
      {showActiveToggle && (
        <label className="flex items-center gap-2 text-sm text-ink">
          <input
            type="checkbox"
            checked={values.is_active}
            onChange={(e) => setValues({ ...values, is_active: e.target.checked })}
          />
          Активен
        </label>
      )}
      <div className="flex gap-2 pt-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? '...' : submitLabel}
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
