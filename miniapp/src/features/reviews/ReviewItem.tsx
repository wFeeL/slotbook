import { Card } from '@/shared/ui/Card';
import { StarRating } from './StarRating';
import type { ReviewRead } from '@/shared/api/types';

interface Props {
  review: ReviewRead;
}

export function ReviewItem({ review }: Props) {
  const created = new Date(review.created_at).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: 'long',
  });
  return (
    <Card surface="shell">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2">
          <div className="text-ink font-semibold text-sm">
            {review.client_first_name ?? 'Гость'}
          </div>
          <StarRating value={review.rating} size="md" />
        </div>
        <div className="text-sienna-deep text-xs">{created}</div>
        {review.text && <div className="text-ink text-sm">{review.text}</div>}
        {review.admin_reply && (
          <div className="rounded-2xl bg-sand/30 p-2 text-sienna-deep text-sm border-l-2 border-rose pl-3">
            <span className="font-semibold">Ответ: </span>
            {review.admin_reply}
          </div>
        )}
      </div>
    </Card>
  );
}
