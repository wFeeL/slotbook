import { Skeleton } from '@/shared/ui/Skeleton';
import { ReviewItem } from './ReviewItem';
import type { ReviewRead } from '@/shared/api/types';

interface Props {
  reviews: ReviewRead[];
  loading?: boolean;
}

export function ReviewsList({ reviews, loading }: Props) {
  if (loading) return <Skeleton height={120} />;
  if (reviews.length === 0) {
    return (
      <p className="text-sienna-deep text-sm text-center py-4">
        Пока нет отзывов. Будьте первым!
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {reviews.map((r) => (
        <ReviewItem key={r.id} review={r} />
      ))}
    </div>
  );
}
