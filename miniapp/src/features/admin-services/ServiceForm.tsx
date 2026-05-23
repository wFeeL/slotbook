// miniapp/src/features/admin-services/ServiceForm.tsx
import { useEffect, useState, type FormEvent } from 'react';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Textarea } from '@/shared/ui/Textarea';
import { Button } from '@/shared/ui/Button';
import { useAdminBranches } from '@/entities/admin-branch/api';

export interface ServiceFormValues {
  branch_id: number | null;
  title: string;
  description: string;
  duration_minutes: number;
  price: string;
  sort_order: number;
  is_active: boolean;
}

interface ServiceFormProps {
  initial?: Partial<ServiceFormValues>;
  submitting?: boolean;
  submitLabel?: string;
  onSubmit(values: ServiceFormValues): void;
  onCancel?: () => void;
}

export function ServiceForm({ initial, submitting, submitLabel = 'Сохранить', onSubmit, onCancel }: ServiceFormProps) {
  const branchesQ = useAdminBranches();
  const activeBranches = (branchesQ.data ?? []).filter((b) => b.is_active);

  const [values, setValues] = useState<ServiceFormValues>({
    branch_id: initial?.branch_id ?? null,
    title: initial?.title ?? '',
    description: initial?.description ?? '',
    duration_minutes: initial?.duration_minutes ?? 60,
    price: initial?.price ?? '',
    sort_order: initial?.sort_order ?? 0,
    is_active: initial?.is_active ?? true,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ServiceFormValues, string>>>({});

  // Default to first active branch once branches load (only when creating, branch_id null)
  useEffect(() => {
    if (values.branch_id == null && activeBranches.length > 0) {
      setValues((v) => ({ ...v, branch_id: activeBranches[0].id }));
    }
  }, [activeBranches, values.branch_id]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const errs: typeof errors = {};
    if (!values.title.trim()) errs.title = 'Введите название';
    if (values.duration_minutes < 5 || values.duration_minutes > 600)
      errs.duration_minutes = 'От 5 до 600 минут';
    if (values.branch_id == null) errs.branch_id = 'Выберите филиал';
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Select
        label="Филиал"
        value={values.branch_id != null ? String(values.branch_id) : ''}
        onChange={(e) =>
          setValues({ ...values, branch_id: e.target.value ? Number(e.target.value) : null })
        }
        error={errors.branch_id ?? null}
        disabled={activeBranches.length === 0}
      >
        {activeBranches.length === 0 && <option value="">Нет филиалов</option>}
        {activeBranches.map((b) => (
          <option key={b.id} value={String(b.id)}>
            {b.name}
          </option>
        ))}
      </Select>
      <Input
        label="Название"
        value={values.title}
        onChange={(e) => setValues({ ...values, title: e.target.value })}
        error={errors.title ?? null}
        placeholder="Например, Стрижка"
      />
      <Textarea
        label="Описание"
        value={values.description}
        onChange={(e) => setValues({ ...values, description: e.target.value })}
        placeholder="Что входит в услугу"
      />
      <Input
        label="Длительность (мин)"
        type="number"
        value={String(values.duration_minutes)}
        onChange={(e) => setValues({ ...values, duration_minutes: Number(e.target.value) })}
        error={errors.duration_minutes ?? null}
        min={5}
        max={600}
      />
      <Input
        label="Цена"
        type="text"
        inputMode="decimal"
        value={values.price}
        onChange={(e) => setValues({ ...values, price: e.target.value })}
        placeholder="1500.00"
      />
      <Input
        label="Порядок"
        type="number"
        value={String(values.sort_order)}
        onChange={(e) => setValues({ ...values, sort_order: Number(e.target.value) })}
      />
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
