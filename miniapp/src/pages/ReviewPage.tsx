import { useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Textarea } from '@/shared/ui/Textarea';
import { StarRating } from '@/features/reviews/StarRating';
import { api } from '@/shared/api/endpoints';
import { pushToast } from '@/shared/store/toast-store';
import { formatLocalDate } from '@/shared/lib/date';

const MAX = 200;

export function ReviewPage() {
  const { bookingId } = useParams();
  const id = bookingId ? Number(bookingId) : 0;
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [rating, setRating] = useState(0);
  const [text, setText] = useState('');

  const ctxQ = useQuery({
    queryKey: ['review-context', id],
    queryFn: () => api.reviews.context(id),
    enabled: id > 0,
    retry: false,
  });

  const mut = useMutation({
    mutationFn: (body: { booking_id: number; rating: number; text?: string | null }) =>
      api.reviews.create(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reviews'] });
      qc.invalidateQueries({ queryKey: ['services'] });
      qc.invalidateQueries({ queryKey: ['staff'] });
      qc.invalidateQueries({ queryKey: ['review-context', id] });
    },
  });

  async function submit() {
    if (rating === 0 || id === 0) return;
    try {
      await mut.mutateAsync({
        booking_id: id,
        rating,
        text: text.trim() || null,
      });
      pushToast('success', 'Спасибо за отзыв!');
      navigate('/my-bookings');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  const ctx = ctxQ.data;
  const existing = ctx?.review ?? null;
  const meta =
    ctx
      ? `${ctx.booking.service_title} · ${formatLocalDate(ctx.booking.starts_at)} · с ${ctx.booking.staff_name}`
      : null;

  return (
    <div className="pt-2 pb-6 px-5 max-w-md mx-auto flex flex-col gap-4">
      <button
        type="button"
        className="self-start text-sienna-deep text-sm"
        onClick={() => navigate(-1)}
      >
        ← Назад
      </button>
      <h1 className="text-2xl text-ink font-display">Как прошла встреча?</h1>
      {meta && <p className="text-sienna-deep text-sm -mt-2">{meta}</p>}

      {ctxQ.isLoading && <Skeleton height={200} />}

      {existing && (
        <Card surface="shell">
          <div className="flex flex-col items-center gap-3 py-4">
            <p className="text-sienna-deep text-sm">Вы уже оценили эту встречу</p>
            <StarRating value={existing.rating} size="lg" />
            {existing.text && (
              <p className="text-ink text-center px-3">{existing.text}</p>
            )}
            {existing.admin_reply && (
              <div className="w-full rounded-2xl bg-sand/30 p-3 text-sienna-deep text-sm border-l-2 border-rose pl-4">
                <span className="font-semibold">Ответ: </span>
                {existing.admin_reply}
              </div>
            )}
          </div>
        </Card>
      )}

      {!existing && !ctxQ.isLoading && (
        <>
          <Card surface="shell">
            <div className="flex flex-col items-center gap-4 py-4">
              <StarRating value={rating} onChange={setRating} size="lg" />
              <Textarea
                value={text}
                onChange={(e) => setText(e.target.value.slice(0, MAX))}
                placeholder="Поделитесь впечатлениями (необязательно)"
              />
              <div className="text-sienna-deep text-xs self-end">
                {text.length}/{MAX}
              </div>
            </div>
          </Card>
          <Button onClick={submit} disabled={rating === 0 || mut.isPending}>
            {mut.isPending ? 'Отправляем…' : 'Отправить'}
          </Button>
        </>
      )}
    </div>
  );
}
