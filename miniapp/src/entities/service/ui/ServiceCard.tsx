import { Card } from '@/shared/ui/Card';
import { formatDuration, formatPrice } from '@/shared/lib/date';
import type { ServiceRead } from '@/shared/api/types';

interface Props {
  service: ServiceRead;
  onSelect: () => void;
}

export function ServiceCard({ service, onSelect }: Props) {
  return (
    <Card interactive onClick={onSelect} role="button" tabIndex={0}>
      <div className="flex flex-col gap-2">
        <span className="text-lg font-semibold text-ink">{service.title}</span>
        {service.description && (
          <span className="text-sm text-sienna">{service.description}</span>
        )}
        <div className="flex items-center gap-3 text-sm tabular-nums">
          <span className="text-sienna">{formatDuration(service.duration_minutes)}</span>
          {service.price && (
            <>
              <span className="text-sand">·</span>
              <span className="text-ink font-semibold">{formatPrice(service.price)}</span>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
