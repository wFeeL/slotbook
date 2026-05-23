// miniapp/src/pages/admin/AdminServiceFormPage.tsx
import { useNavigate, useParams } from 'react-router';
import { useEffect, useState } from 'react';
import { ServiceForm, type ServiceFormValues } from '@/features/admin-services/ServiceForm';
import { useAdminServices, useArchiveService, useCreateService, useUpdateServiceById } from '@/entities/admin-service/api';
import { pushToast } from '@/shared/store/toast-store';
import { useHaptic } from '@/shared/telegram/hooks';
import { Button } from '@/shared/ui/Button';

export function AdminServiceFormPage() {
  const navigate = useNavigate();
  const params = useParams();
  const haptic = useHaptic();
  const isEdit = Boolean(params.id);
  const id = params.id ? Number(params.id) : null;

  const services = useAdminServices();
  const existing = isEdit && id != null ? (services.data ?? []).find((s) => s.id === id) : null;
  const [initial, setInitial] = useState<Partial<ServiceFormValues> | null>(isEdit ? null : {});

  useEffect(() => {
    if (isEdit && existing) {
      setInitial({
        title: existing.title,
        description: existing.description ?? '',
        duration_minutes: existing.duration_minutes,
        price: existing.price ?? '',
        sort_order: existing.sort_order,
        is_active: existing.is_active,
      });
    }
  }, [isEdit, existing]);

  const create = useCreateService();
  const update = useUpdateServiceById();
  const archive = useArchiveService();

  async function handleSubmit(values: ServiceFormValues) {
    try {
      if (isEdit && id != null) {
        await update.mutateAsync({
          id,
          patch: {
            title: values.title,
            description: values.description || null,
            duration_minutes: values.duration_minutes,
            price: values.price || null,
            sort_order: values.sort_order,
            is_active: values.is_active,
          },
        });
      } else {
        await create.mutateAsync({
          title: values.title,
          description: values.description || null,
          duration_minutes: values.duration_minutes,
          price: values.price || null,
          sort_order: values.sort_order,
        });
      }
      pushToast('success', 'Сохранено');
      haptic.success();
      navigate('/admin/services');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось сохранить');
      haptic.error();
    }
  }

  async function handleArchive() {
    if (id == null) return;
    try {
      await archive.mutateAsync(id);
      pushToast('success', 'Услуга архивирована');
      navigate('/admin/services');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  if (isEdit && initial === null) {
    return <div className="text-sienna text-sm">Загрузка…</div>;
  }

  return (
    <div className="pt-2 pb-6">
      <h2 className="text-xl text-ink font-display mb-4">
        {isEdit ? 'Редактировать услугу' : 'Новая услуга'}
      </h2>
      <ServiceForm
        initial={initial ?? {}}
        submitting={create.isPending || update.isPending}
        onSubmit={handleSubmit}
        onCancel={() => navigate('/admin/services')}
      />
      {isEdit && (
        <div className="mt-6 pt-4 border-t border-sand">
          <Button variant="ghost" onClick={handleArchive} disabled={archive.isPending}>
            Архивировать
          </Button>
        </div>
      )}
    </div>
  );
}
