import { useMutation } from '@tanstack/react-query';
import { Button } from '@/shared/ui/Button';
import { api } from '@/shared/api/endpoints';
import { pushToast } from '@/shared/store/toast-store';
import { getWebApp } from '@/shared/telegram/webapp';

interface Props {
  ownerType: 'service' | 'staff';
  ownerId: number;
}

export function PhotoUploadButton({ ownerType, ownerId }: Props) {
  const mut = useMutation({
    mutationFn: () =>
      api.admin.photos.createUploadIntent({ owner_type: ownerType, owner_id: ownerId }),
  });

  async function handle() {
    try {
      const { bot_url } = await mut.mutateAsync();
      const tg = getWebApp();
      if (tg && typeof tg.openTelegramLink === 'function') {
        tg.openTelegramLink(bot_url);
      } else {
        window.location.href = bot_url;
      }
      pushToast('success', 'Откройте чат с ботом и пришлите фото');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <Button onClick={handle} disabled={mut.isPending} variant="secondary">
      📷 Загрузить фото
    </Button>
  );
}
