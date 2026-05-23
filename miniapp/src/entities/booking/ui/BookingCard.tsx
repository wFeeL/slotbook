import { Card } from '@/shared/ui/Card';
import { cn } from '@/shared/lib/cn';
import { formatLocalDate, formatLocalTime } from '@/shared/lib/date';
import type { BookingRead } from '@/shared/api/types';
import { bookingStatusLabel, bookingStatusTone } from '../lib/status';

interface Props {
  booking: BookingRead;
  onSelect?: () => void;
}

const TONE_TEXT: Record<ReturnType<typeof bookingStatusTone>, string> = {
  sage: 'text-sage',
  clay: 'text-clay',
  sienna: 'text-sienna',
  rose: 'text-rose-deep',
  sand: 'text-sienna',
};

export function BookingCard({ booking, onSelect }: Props) {
  const tone = bookingStatusTone(booking.status);
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
        <span className={cn('text-sm font-semibold', TONE_TEXT[tone])}>
          {bookingStatusLabel(booking.status)}
        </span>
      </div>
    </Card>
  );
}
