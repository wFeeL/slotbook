import { useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Textarea } from '@/shared/ui/Textarea';
import { StarRating } from '@/features/reviews/StarRating';
import { api } from '@/shared/api/endpoints';
import { pushToast } from '@/shared/store/toast-store';

const MAX = 200;

export function ReviewPage() {
  const { bookingId } = useParams();
  const id = bookingId ? Number(bookingId) : 0;
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [rating, setRating] = useState(0);
  const [text, setText] = useState('');

  const mut = useMutation({
    mutationFn: (body: { booking_id: number; rating: number; text?: string | null }) =>
      api.reviews.create(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reviews'] });
      qc.invalidateQueries({ queryKey: ['services'] });
      qc.invalidateQueries({ queryKey: ['staff'] });
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
    </div>
  );
}
