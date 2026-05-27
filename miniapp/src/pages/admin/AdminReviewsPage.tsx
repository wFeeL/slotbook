import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Badge } from '@/shared/ui/Badge';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Sheet } from '@/shared/ui/Sheet';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Textarea } from '@/shared/ui/Textarea';
import { api } from '@/shared/api/endpoints';
import { StarRating } from '@/features/reviews/StarRating';
import { pushToast } from '@/shared/store/toast-store';
import { showConfirm } from '@/shared/telegram/hooks';
import type { ReviewRead } from '@/shared/api/types';

const KEY = ['admin', 'reviews'] as const;

export function AdminReviewsPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'hidden' | 'visible'>('all');
  const params = filter === 'all' ? {} : { hidden: filter === 'hidden' };
  const q = useQuery({
    queryKey: [...KEY, filter],
    queryFn: () => api.admin.reviews.list({ ...params, limit: 100 }),
  });

  const hideM = useMutation({
    mutationFn: (id: number) => api.admin.reviews.hide(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
  const unhideM = useMutation({
    mutationFn: (id: number) => api.admin.reviews.unhide(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
  const replyM = useMutation({
    mutationFn: (args: { id: number; text: string }) =>
      api.admin.reviews.reply(args.id, args.text),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
  const delM = useMutation({
    mutationFn: (id: number) => api.admin.reviews.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });

  const [replyTo, setReplyTo] = useState<number | null>(null);
  const [replyText, setReplyText] = useState('');

  async function toggleHide(r: ReviewRead) {
    try {
      if (r.is_hidden) await unhideM.mutateAsync(r.id);
      else await hideM.mutateAsync(r.id);
      pushToast('success', r.is_hidden ? 'Видно' : 'Скрыто');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function deleteReview(r: ReviewRead) {
    const ok = await showConfirm('Удалить отзыв навсегда?');
    if (!ok) return;
    try {
      await delM.mutateAsync(r.id);
      pushToast('success', 'Удалено');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function saveReply() {
    if (replyTo === null || replyText.trim() === '') return;
    try {
      await replyM.mutateAsync({ id: replyTo, text: replyText });
      pushToast('success', 'Ответ сохранён');
      setReplyTo(null);
      setReplyText('');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <div className="pt-2 pb-6 flex flex-col gap-4">
      <header className="flex items-center justify-between">
        <h2 className="text-xl text-ink font-display">Отзывы</h2>
      </header>

      <div className="flex gap-2">
        {(['all', 'visible', 'hidden'] as const).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFilter(f)}
            className={
              filter === f
                ? 'rounded-full px-3 py-1 text-sm font-semibold bg-rose text-shell'
                : 'rounded-full px-3 py-1 text-sm font-semibold bg-shell border border-sand text-sienna-deep'
            }
          >
            {f === 'all' ? 'Все' : f === 'visible' ? 'Видимые' : 'Скрытые'}
          </button>
        ))}
      </div>

      {q.isLoading && <Skeleton height={120} />}
      {q.data?.length === 0 && (
        <p className="text-sienna-deep text-sm">Отзывов нет.</p>
      )}
      {q.data?.map((r) => (
        <Card key={r.id} surface="shell">
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between gap-2">
              <div className="text-ink font-semibold text-sm">
                {r.client_first_name ?? 'Гость'}
              </div>
              <div className="flex items-center gap-2">
                <StarRating value={r.rating} />
                {r.is_hidden && <Badge tone="clay">скрыт</Badge>}
              </div>
            </div>
            {r.text && <div className="text-ink text-sm">{r.text}</div>}
            {r.admin_reply && (
              <div className="rounded-2xl bg-sand/30 p-2 text-sienna-deep text-sm border-l-2 border-rose pl-3">
                <span className="font-semibold">Ответ: </span>
                {r.admin_reply}
              </div>
            )}
            <div className="flex gap-2 flex-wrap pt-1">
              <Button size="md" variant="secondary" onClick={() => toggleHide(r)}>
                {r.is_hidden ? 'Показать' : 'Скрыть'}
              </Button>
              <Button
                size="md"
                variant="secondary"
                onClick={() => {
                  setReplyTo(r.id);
                  setReplyText(r.admin_reply ?? '');
                }}
              >
                Ответить
              </Button>
              <Button variant="ghost" onClick={() => deleteReview(r)}>
                Удалить
              </Button>
            </div>
          </div>
        </Card>
      ))}

      <Sheet
        open={replyTo !== null}
        onClose={() => setReplyTo(null)}
        title="Ответ на отзыв"
      >
        <div className="flex flex-col gap-3">
          <Textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="Спасибо за отзыв! Будем ждать вас снова."
          />
          <div className="flex gap-2">
            <Button
              onClick={saveReply}
              disabled={replyM.isPending || replyText.trim() === ''}
            >
              Сохранить
            </Button>
            <Button variant="secondary" onClick={() => setReplyTo(null)}>
              Отмена
            </Button>
          </div>
        </div>
      </Sheet>
    </div>
  );
}
