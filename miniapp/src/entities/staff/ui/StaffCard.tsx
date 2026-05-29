import { useNavigate } from 'react-router';
import { Card } from '@/shared/ui/Card';
import { RatingBadge } from '@/features/reviews/RatingBadge';
import type { StaffRead } from '@/shared/api/types';

interface Props {
  staff: StaffRead;
  onSelect: () => void;
}

export function StaffCard({ staff, onSelect }: Props) {
  const navigate = useNavigate();
  const avatar = (staff.photos ?? [])[0];

  function openDetail(e: React.MouseEvent | React.KeyboardEvent) {
    e.stopPropagation();
    navigate(`/staff/${staff.id}`);
  }

  return (
    <Card interactive onClick={onSelect} role="button" tabIndex={0}>
      <div className="flex items-center gap-4">
        {avatar ? (
          <img
            src={avatar.url}
            alt=""
            loading="lazy"
            className="w-10 h-10 rounded-full object-cover bg-sand/40 shrink-0"
          />
        ) : (
          <div
            className="w-10 h-10 rounded-full bg-sand text-ink flex items-center justify-center text-base font-semibold shrink-0"
            aria-hidden
          >
            {staff.name[0]}
          </div>
        )}
        <div className="flex flex-col flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <span className="text-lg font-semibold text-ink">{staff.name}</span>
            <button
              type="button"
              onClick={openDetail}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && openDetail(e)}
              className="shrink-0 text-sienna-deep text-sm font-semibold leading-none p-1 -m-1"
              aria-label="Профиль мастера"
            >
              ⓘ
            </button>
          </div>
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
