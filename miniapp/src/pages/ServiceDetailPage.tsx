import { useNavigate, useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { api } from '@/shared/api/endpoints';
import { PhotoGallery } from '@/features/photos/PhotoGallery';
import { RatingBadge } from '@/features/reviews/RatingBadge';
import { ReviewsList } from '@/features/reviews/ReviewsList';
import { useBookingFlowStore } from '@/shared/store/booking-flow-store';

export function ServiceDetailPage() {
  const { id } = useParams();
  const sid = id ? Number(id) : 0;
  const navigate = useNavigate();
  const setService = useBookingFlowStore((s) => s.setService);

  const q = useQuery({
    queryKey: ['service', sid],
    queryFn: () => api.services.get(sid),
    enabled: sid > 0,
  });
  const reviews = useQuery({
    queryKey: ['reviews', 'service', sid],
    queryFn: () => api.reviews.listForService(sid, { limit: 20 }),
    enabled: sid > 0,
  });

  if (q.isLoading)
    return (
      <div className="p-5">
        <Skeleton height={300} />
      </div>
    );
  if (!q.data) return <p className="p-5 text-sienna-deep">Услуга не найдена.</p>;
  const svc = q.data;

  return (
    <div className="pt-2 pb-24 px-5 max-w-md mx-auto flex flex-col gap-4">
      <button
        type="button"
        className="self-start text-sienna-deep text-sm"
        onClick={() => navigate(-1)}
      >
        ← Назад
      </button>

      <PhotoGallery photos={svc.photos ?? []} />

      <header className="flex flex-col gap-1">
        <h1 className="text-2xl text-ink font-display">{svc.title}</h1>
        <div className="flex items-center gap-3">
          <span className="text-sienna-deep text-sm">
            {svc.duration_minutes} мин
            {svc.price && ` · ${svc.price} ₽`}
          </span>
          <RatingBadge rating={svc.avg_rating ?? null} count={svc.review_count ?? 0} />
        </div>
      </header>

      {svc.description && (
        <Card surface="shell">
          <p className="text-ink leading-relaxed">{svc.description}</p>
        </Card>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="text-ink font-display text-lg">Отзывы</h2>
        <ReviewsList reviews={reviews.data ?? []} loading={reviews.isLoading} />
      </section>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-cream/95 backdrop-blur border-t border-sand">
        <Button
          className="w-full"
          onClick={() => {
            setService(svc.id);
            navigate('/book/staff');
          }}
        >
          Записаться
        </Button>
      </div>
    </div>
  );
}
