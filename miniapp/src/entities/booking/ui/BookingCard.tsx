import { Card } from '@/shared/ui/Card';
import { cn } from '@/shared/lib/cn';
import { formatLocalDate, formatLocalTime } from '@/shared/lib/date';
import type { BookingRead } from '@/shared/api/types';

interface Props {
  booking: BookingRead;
  onSelect?: () => void;
}

const STATUS_LABEL: Record<BookingRead['status'], { text: string; color: string }> = {
  pending: { text: 'Ожидает', color: 'text-clay' },
  confirmed: { text: 'Подтверждена', color: 'text-sage' },
  completed: { text: 'Завершена', color: 'text-sienna' },
  cancelled_by_client: { text: 'Отменена', color: 'text-sienna' },
  cancelled_by_admin: { text: 'Отменена администратором', color: 'text-sienna' },
  no_show: { text: 'Не пришли', color: 'text-clay' },
  rescheduled: { text: 'Перенесена', color: 'text-sienna' },
};

export function BookingCard({ booking, onSelect }: Props) {
  const status = STATUS_LABEL[booking.status];
  return (
    <Card
      interactive={Boolean(onSelect)}
      onClick={onSelect}
      role={onSelect ? 'button' : undefined}
      tabIndex={onSelect ? 0 : undefined}
    >
      <div className="flex flex-col gap-2">
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-lg font-semibold text-ink">
            {formatLocalDate(booking.starts_at)}
          </span>
          <span className="text-base tabular-nums text-sienna">
            {formatLocalTime(booking.starts_at)}
          </span>
        </div>
        <span className={cn('text-sm font-semibold', status.color)}>{status.text}</span>
      </div>
    </Card>
  );
}
