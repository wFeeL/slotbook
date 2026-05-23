import { useState } from 'react';
import { Sheet } from '@/shared/ui/Sheet';
import { Select } from '@/shared/ui/Select';
import { Button } from '@/shared/ui/Button';
import { useCreateInvite } from '@/entities/admin-team/api';
import { pushToast } from '@/shared/store/toast-store';

export function InviteSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [role, setRole] = useState<'admin' | 'staff'>('admin');
  const [ttl, setTtl] = useState<24 | 168 | 720>(168);
  const create = useCreateInvite();
  const [url, setUrl] = useState<string | null>(null);

  async function submit() {
    try {
      const inv = await create.mutateAsync({ role, ttl_hours: ttl });
      setUrl(inv.url);
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function copy() {
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      pushToast('success', 'Ссылка скопирована');
    } catch {
      pushToast('error', 'Не удалось скопировать');
    }
  }

  function close() {
    setUrl(null);
    setRole('admin');
    setTtl(168);
    onClose();
  }

  return (
    <Sheet open={open} onClose={close} title="Создать приглашение">
      {url ? (
        <div className="flex flex-col gap-3">
          <p className="text-ink text-sm">Отправьте эту ссылку через Telegram:</p>
          <div className="rounded-2xl bg-shell border border-sand p-3 text-sm break-all">{url}</div>
          <div className="flex gap-2">
            <Button onClick={copy}>Скопировать</Button>
            <Button variant="secondary" onClick={close}>
              Готово
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <Select
            label="Роль"
            value={role}
            onChange={(e) => setRole(e.target.value as 'admin' | 'staff')}
          >
            <option value="admin">Администратор</option>
            <option value="staff">Сотрудник</option>
          </Select>
          <Select
            label="Срок действия"
            value={String(ttl)}
            onChange={(e) => setTtl(Number(e.target.value) as 24 | 168 | 720)}
          >
            <option value="24">24 часа</option>
            <option value="168">7 дней</option>
            <option value="720">30 дней</option>
          </Select>
          <Button onClick={submit} disabled={create.isPending}>
            {create.isPending ? '...' : 'Создать'}
          </Button>
        </div>
      )}
    </Sheet>
  );
}
