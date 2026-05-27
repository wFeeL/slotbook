interface Props {
  rating: number | null | undefined;
  count: number;
  size?: 'sm' | 'md';
}

export function RatingBadge({ rating, count, size = 'sm' }: Props) {
  const ts = size === 'sm' ? 'text-xs' : 'text-sm';
  if (rating == null || count === 0) {
    return <span className={`text-sienna-deep ${ts}`}>★ Нет оценок</span>;
  }
  return (
    <span className={`${ts}`}>
      <span className="text-rose">★</span>{' '}
      <span className="text-ink font-semibold">{rating.toFixed(1)}</span>
      <span className="text-sienna-deep"> · {count}</span>
    </span>
  );
}
