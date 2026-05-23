// miniapp/src/features/admin-staff/StaffForm.tsx
import { useState, type FormEvent } from 'react';
import { Input } from '@/shared/ui/Input';
import { Textarea } from '@/shared/ui/Textarea';
import { Button } from '@/shared/ui/Button';

export interface StaffFormValues {
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
  const [values, setValues] = useState<StaffFormValues>({
    name: initial?.name ?? '',
    description: initial?.description ?? '',
  });
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!values.name.trim()) {
      setError('Введите имя');
      return;
    }
    setError(null);
    onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Input
        label="Имя"
        value={values.name}
        onChange={(e) => setValues({ ...values, name: e.target.value })}
        error={error}
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
