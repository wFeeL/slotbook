import { cn } from '@/shared/lib/cn';
import { formatLocalTime } from '@/shared/lib/date';

interface Props {
  startsAt: string;
  selected: boolean;
  onSelect: () => void;
}

export function SlotChip({ startsAt, selected, onSelect }: Props) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        'rounded-2xl px-3 py-3 text-base tabular-nums font-semibold transition active:scale-[0.97]',
        'border border-sand',
        selected
          ? 'bg-rose text-white border-rose shadow-warm'
          : 'bg-shell text-ink hover:bg-sand/30',
      )}
    >
      {formatLocalTime(startsAt)}
    </button>
  );
}
