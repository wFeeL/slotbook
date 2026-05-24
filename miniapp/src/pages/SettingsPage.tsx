import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Toggle } from '@/shared/ui/Toggle';
import { api } from '@/shared/api/endpoints';
import { pushToast } from '@/shared/store/toast-store';

export function SettingsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const me = useQuery({
    queryKey: ['me'],
    queryFn: () => api.me.get(),
  });
  const [enabled, setEnabled] = useState<boolean>(true);
  useEffect(() => {
    if (me.data) setEnabled(me.data.reminders_enabled);
  }, [me.data]);

  const patch = useMutation({
    mutationFn: (value: boolean) => api.me.patchPreferences({ reminders_enabled: value }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['me'] }),
  });

  async function toggle(value: boolean) {
    setEnabled(value);
    try {
      await patch.mutateAsync(value);
      pushToast('success', value ? 'Напоминания включены' : 'Напоминания выключены');
    } catch (e) {
      setEnabled(!value); // revert
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <div className="pt-2 pb-6 px-5 max-w-md mx-auto flex flex-col gap-4">
      <header className="flex flex-col gap-1">
        <button
          type="button"
          className="self-start text-sienna-deep text-sm"
          onClick={() => navigate('/')}
        >
          ← На главную
        </button>
        <h1 className="text-xl text-ink font-display">Настройки</h1>
      </header>

      {me.isLoading && <Skeleton height={120} />}
      {me.data && (
        <Card surface="shell">
          <div className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="text-ink font-semibold">Напоминания о записи</div>
                <div className="text-sienna-deep text-sm mt-1">
                  Бот пришлёт два напоминания: за сутки и за час до встречи. Можно
                  выключить, если уведомления мешают.
                </div>
              </div>
              <Toggle checked={enabled} onChange={toggle} />
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
