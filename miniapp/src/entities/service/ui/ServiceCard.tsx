import { useNavigate } from 'react-router';
import { Card } from '@/shared/ui/Card';
import { RatingBadge } from '@/features/reviews/RatingBadge';
import { formatDuration, formatPrice } from '@/shared/lib/date';
import type { ServiceRead } from '@/shared/api/types';

interface Props {
  service: ServiceRead;
  onSelect: () => void;
}

export function ServiceCard({ service, onSelect }: Props) {
  const navigate = useNavigate();
  const thumb = (service.photos ?? [])[0];

  function openDetail(e: React.MouseEvent | React.KeyboardEvent) {
    e.stopPropagation();
    navigate(`/services/${service.id}`);
  }

  return (
    <Card interactive onClick={onSelect} role="button" tabIndex={0}>
      <div className="flex items-start gap-3">
        {thumb ? (
          <img
            src={thumb.url}
            alt=""
            loading="lazy"
            className="w-14 h-14 rounded-2xl object-cover bg-sand/40 shrink-0"
          />
        ) : (
          <div
            className="w-14 h-14 rounded-2xl bg-sand/40 shrink-0"
            aria-hidden
          />
        )}
        <div className="flex flex-col gap-1 flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <span className="text-lg font-semibold text-ink">{service.title}</span>
            <button
              type="button"
              onClick={openDetail}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && openDetail(e)}
              className="shrink-0 text-sienna-deep text-sm font-semibold leading-none p-1 -m-1"
              aria-label="Подробнее об услуге"
            >
              ⓘ
            </button>
          </div>
          {service.description && (
            <span className="text-sm text-sienna-deep line-clamp-2">
              {service.description}
            </span>
          )}
          <div className="flex items-center gap-3 text-sm tabular-nums">
            <span className="text-sienna-deep">{formatDuration(service.duration_minutes)}</span>
            {service.price && (
              <>
                <span className="text-sand">·</span>
                <span className="text-ink font-semibold">{formatPrice(service.price)}</span>
              </>
            )}
          </div>
          <RatingBadge
            rating={service.avg_rating ?? null}
            count={service.review_count ?? 0}
          />
        </div>
      </div>
    </Card>
  );
}
