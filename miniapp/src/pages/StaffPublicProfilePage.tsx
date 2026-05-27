import { useNavigate, useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { api } from '@/shared/api/endpoints';
import { PhotoGallery } from '@/features/photos/PhotoGallery';
import { RatingBadge } from '@/features/reviews/RatingBadge';
import { ReviewsList } from '@/features/reviews/ReviewsList';

export function StaffPublicProfilePage() {
  const { id } = useParams();
  const sid = id ? Number(id) : 0;
  const navigate = useNavigate();

  const q = useQuery({
    queryKey: ['staff', sid],
    queryFn: () => api.staff.get(sid),
    enabled: sid > 0,
  });
  const reviews = useQuery({
    queryKey: ['reviews', 'staff', sid],
    queryFn: () => api.reviews.listForStaff(sid, { limit: 20 }),
    enabled: sid > 0,
  });

  if (q.isLoading)
    return (
      <div className="p-5">
        <Skeleton height={300} />
      </div>
    );
  if (!q.data) return <p className="p-5 text-sienna-deep">Мастер не найден.</p>;
  const stf = q.data;

  return (
    <div className="pt-2 pb-6 px-5 max-w-md mx-auto flex flex-col gap-4">
      <button
        type="button"
        className="self-start text-sienna-deep text-sm"
        onClick={() => navigate(-1)}
      >
        ← Назад
      </button>

      <PhotoGallery photos={stf.photos ?? []} />

      <header className="flex flex-col gap-1">
        <h1 className="text-2xl text-ink font-display">{stf.name}</h1>
        <RatingBadge rating={stf.avg_rating ?? null} count={stf.review_count ?? 0} />
      </header>

      {stf.description && (
        <Card surface="shell">
          <p className="text-ink leading-relaxed">{stf.description}</p>
        </Card>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="text-ink font-display text-lg">Отзывы клиентов</h2>
        <ReviewsList reviews={reviews.data ?? []} loading={reviews.isLoading} />
      </section>
    </div>
  );
}
