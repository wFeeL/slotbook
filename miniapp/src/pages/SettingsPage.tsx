import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Input } from '@/shared/ui/Input';
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
  const [phone, setPhone] = useState<string>('');
  useEffect(() => {
    if (me.data) {
      setEnabled(me.data.reminders_enabled);
      setPhone(me.data.phone ?? '');
    }
  }, [me.data]);

  const patchPrefs = useMutation({
    mutationFn: (value: boolean) => api.me.patchPreferences({ reminders_enabled: value }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['me'] }),
  });

  const patchProfile = useMutation({
    mutationFn: (newPhone: string | null) => api.me.patchProfile({ phone: newPhone }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['me'] }),
  });

  async function toggle(value: boolean) {
    setEnabled(value);
    try {
      await patchPrefs.mutateAsync(value);
      pushToast('success', value ? 'Напоминания включены' : 'Напоминания выключены');
    } catch (e) {
      setEnabled(!value);
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function savePhone() {
    try {
      await patchProfile.mutateAsync(phone.trim() || null);
      pushToast('success', 'Телефон сохранён');
    } catch (e) {
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
        <>
          <Card surface="shell">
            <div className="flex flex-col gap-3">
              <div className="text-sienna-deep text-xs uppercase tracking-wide">
                Контактный телефон
              </div>
              <Input
                type="tel"
                placeholder="+7 999 000-00-00"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
              <p className="text-sienna-deep text-xs">
                По телефону мастер сможет связаться с вами, если возникнут вопросы
                по записи. Telegram ID для этого не подходит.
              </p>
              <Button
                size="md"
                onClick={savePhone}
                disabled={patchProfile.isPending || (me.data.phone ?? '') === phone.trim()}
              >
                Сохранить
              </Button>
            </div>
          </Card>

          <Card surface="shell">
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
          </Card>
        </>
      )}
    </div>
  );
}
