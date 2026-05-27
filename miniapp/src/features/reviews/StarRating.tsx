interface Props {
  value: number;
  onChange?: (value: number) => void;
  size?: 'md' | 'lg';
}

export function StarRating({ value, onChange, size = 'md' }: Props) {
  const sz = size === 'lg' ? 'text-4xl' : 'text-2xl';
  const stars = [1, 2, 3, 4, 5];

  if (!onChange) {
    return (
      <div className={`flex gap-1 ${sz}`}>
        {stars.map((s) => (
          <span
            key={s}
            data-filled={s <= value}
            className={s <= value ? 'text-rose' : 'text-sand'}
          >
            ★
          </span>
        ))}
      </div>
    );
  }

  return (
    <div className={`flex gap-1 ${sz}`}>
      {stars.map((s) => (
        <button
          key={s}
          type="button"
          aria-label={`${s} stars`}
          onClick={() => onChange(s)}
          className={
            s <= value
              ? 'text-rose hover:scale-110 transition'
              : 'text-sand hover:scale-110 transition'
          }
        >
          ★
        </button>
      ))}
    </div>
  );
}
