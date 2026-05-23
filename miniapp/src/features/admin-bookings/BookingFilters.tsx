import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';

export interface FilterValues {
  date: string;
  status: string;
}

interface BookingFiltersProps {
  values: FilterValues;
  onChange(values: FilterValues): void;
}

export function BookingFilters({ values, onChange }: BookingFiltersProps) {
  return (
    <div className="flex flex-col gap-2">
      <Input
        label="Дата"
        type="date"
        value={values.date}
        onChange={(e) => onChange({ ...values, date: e.target.value })}
      />
      <Select
        label="Статус"
        value={values.status}
        onChange={(e) => onChange({ ...values, status: e.target.value })}
      >
        <option value="">Все</option>
        <option value="pending">В ожидании</option>
        <option value="confirmed">Подтверждено</option>
        <option value="cancelled_by_client">Отменено клиентом</option>
        <option value="cancelled_by_admin">Отменено админом</option>
        <option value="completed">Завершено</option>
        <option value="no_show">Не пришёл</option>
      </Select>
    </div>
  );
}
