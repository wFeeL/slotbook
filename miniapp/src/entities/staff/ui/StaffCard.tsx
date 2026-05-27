import { Card } from '@/shared/ui/Card';
import { RatingBadge } from '@/features/reviews/RatingBadge';
import type { StaffRead } from '@/shared/api/types';

interface Props {
  staff: StaffRead;
  onSelect: () => void;
}

export function StaffCard({ staff, onSelect }: Props) {
  const avatar = (staff.photos ?? [])[0];
  return (
    <Card interactive onClick={onSelect} role="button" tabIndex={0}>
      <div className="flex items-center gap-4">
        {avatar ? (
          <img
            src={avatar.url}
            alt=""
            loading="lazy"
            className="w-12 h-12 rounded-full object-cover bg-sand/40 shrink-0"
          />
        ) : (
          <div
            className="w-12 h-12 rounded-full bg-sand text-ink flex items-center justify-center text-lg font-semibold shrink-0"
            aria-hidden
          >
            {staff.name[0]}
          </div>
        )}
        <div className="flex flex-col flex-1 min-w-0">
          <span className="text-lg font-semibold text-ink">{staff.name}</span>
          {staff.description && (
            <span className="text-sm text-sienna-deep line-clamp-2">
              {staff.description}
            </span>
          )}
          <RatingBadge
            rating={staff.avg_rating ?? null}
            count={staff.review_count ?? 0}
          />
        </div>
      </div>
    </Card>
  );
}
