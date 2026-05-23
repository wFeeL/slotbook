import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { Select } from '@/shared/ui/Select';

interface Props {
  value: number | null;
  onChange: (value: number | null) => void;
  currentUserId: number | null;
}

export function UserLinkField({ value, onChange, currentUserId }: Props) {
  const q = useQuery({
    queryKey: ['admin', 'users', 'linkable', currentUserId],
    queryFn: () =>
      api.admin.users.list({
        role: 'staff',
        linkable_only: true,
        include_user_id: currentUserId ?? undefined,
      }),
  });

  return (
    <Select
      label="Связать с пользователем Telegram"
      value={value === null ? '' : String(value)}
      onChange={(e) => {
        const v = e.target.value;
        onChange(v === '' ? null : Number(v));
      }}
    >
      <option value="">Не связан</option>
      {q.data?.map((u) => {
        const name =
          [u.first_name, u.last_name].filter(Boolean).join(' ') || `TG ${u.telegram_id}`;
        const usernameSuffix = u.username ? ` @${u.username}` : '';
        return (
          <option key={u.id} value={u.id}>
            {`${name}${usernameSuffix}`}
          </option>
        );
      })}
    </Select>
  );
}
