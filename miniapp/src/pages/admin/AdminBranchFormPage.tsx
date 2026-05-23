import { useNavigate, useParams } from 'react-router';
import { useEffect, useState } from 'react';
import { BranchForm, type BranchFormValues } from '@/features/admin-branches/BranchForm';
import {
  useAdminBranches,
  useArchiveBranch,
  useCreateBranch,
  useUpdateBranch,
} from '@/entities/admin-branch/api';
import { pushToast } from '@/shared/store/toast-store';
import { useHaptic } from '@/shared/telegram/hooks';
import { Button } from '@/shared/ui/Button';

export function AdminBranchFormPage() {
  const navigate = useNavigate();
  const params = useParams();
  const haptic = useHaptic();
  const isEdit = Boolean(params.id);
  const id = params.id ? Number(params.id) : null;

  const branches = useAdminBranches();
  const existing = isEdit && id != null ? (branches.data ?? []).find((b) => b.id === id) : null;
  const [initial, setInitial] = useState<Partial<BranchFormValues> | null>(isEdit ? null : {});

  useEffect(() => {
    if (isEdit && existing) {
      setInitial({
        name: existing.name,
        address: existing.address ?? '',
        timezone: existing.timezone,
        sort_order: existing.sort_order,
        is_active: existing.is_active,
      });
    }
  }, [isEdit, existing]);

  const create = useCreateBranch();
  const update = useUpdateBranch();
  const archive = useArchiveBranch();

  async function handleSubmit(values: BranchFormValues) {
    try {
      if (isEdit && id != null) {
        await update.mutateAsync({
          id,
          patch: {
            name: values.name,
            address: values.address || null,
            timezone: values.timezone,
            sort_order: values.sort_order,
            is_active: values.is_active,
          },
        });
      } else {
        await create.mutateAsync({
          name: values.name,
          address: values.address || null,
          timezone: values.timezone,
          sort_order: values.sort_order,
        });
      }
      pushToast('success', 'Сохранено');
      haptic.success();
      navigate('/admin/branches');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось сохранить');
      haptic.error();
    }
  }

  async function handleArchive() {
    if (id == null) return;
    try {
      await archive.mutateAsync(id);
      pushToast('success', 'Филиал архивирован');
      navigate('/admin/branches');
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
        {isEdit ? 'Редактировать филиал' : 'Новый филиал'}
      </h2>
      <BranchForm
        initial={initial ?? {}}
        submitting={create.isPending || update.isPending}
        showActiveToggle={isEdit}
        onSubmit={handleSubmit}
        onCancel={() => navigate('/admin/branches')}
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
