// miniapp/src/features/admin-staff/StaffForm.tsx
import { useEffect, useState, type FormEvent } from 'react';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Textarea } from '@/shared/ui/Textarea';
import { Button } from '@/shared/ui/Button';
import { useAdminBranches } from '@/entities/admin-branch/api';

export interface StaffFormValues {
  branch_id: number | null;
  name: string;
  description: string;
}

interface StaffFormProps {
  initial?: Partial<StaffFormValues>;
  submitting?: boolean;
  submitLabel?: string;
  onSubmit(values: StaffFormValues): void;
  onCancel?: () => void;
}

export function StaffForm({ initial, submitting, submitLabel = 'Сохранить', onSubmit, onCancel }: StaffFormProps) {
  const branchesQ = useAdminBranches();
  const activeBranches = (branchesQ.data ?? []).filter((b) => b.is_active);

  const [values, setValues] = useState<StaffFormValues>({
    branch_id: initial?.branch_id ?? null,
    name: initial?.name ?? '',
    description: initial?.description ?? '',
  });
  const [errors, setErrors] = useState<{ name?: string | null; branch_id?: string | null }>({});

  useEffect(() => {
    if (values.branch_id == null && activeBranches.length > 0) {
      setValues((v) => ({ ...v, branch_id: activeBranches[0].id }));
    }
  }, [activeBranches, values.branch_id]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const errs: typeof errors = {};
    if (!values.name.trim()) errs.name = 'Введите имя';
    if (values.branch_id == null) errs.branch_id = 'Выберите филиал';
    setErrors(errs);
    if (Object.keys(errs).filter((k) => (errs as Record<string, string | null>)[k]).length > 0)
      return;
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
        label="Имя"
        value={values.name}
        onChange={(e) => setValues({ ...values, name: e.target.value })}
        error={errors.name ?? null}
      />
      <Textarea
        label="Описание"
        value={values.description}
        onChange={(e) => setValues({ ...values, description: e.target.value })}
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
