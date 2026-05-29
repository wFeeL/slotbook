import { useRef, type KeyboardEvent } from 'react';

interface Props {
  value: number;
  onChange?: (value: number) => void;
  size?: 'md' | 'lg';
}

export function StarRating({ value, onChange, size = 'md' }: Props) {
  const sz = size === 'lg' ? 'text-4xl' : 'text-2xl';
  const stars = [1, 2, 3, 4, 5];
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  if (!onChange) {
    return (
      <div className={`flex gap-1 ${sz}`} role="img" aria-label={`Оценка ${value} из 5`}>
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

  function focusStar(i: number) {
    const clamped = Math.max(0, Math.min(4, i));
    refs.current[clamped]?.focus();
  }

  function handleKey(e: KeyboardEvent<HTMLButtonElement>, s: number) {
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
      e.preventDefault();
      const next = Math.min(5, s + 1);
      onChange!(next);
      focusStar(next - 1);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
      e.preventDefault();
      const next = Math.max(1, s - 1);
      onChange!(next);
      focusStar(next - 1);
    } else if (e.key === 'Home') {
      e.preventDefault();
      onChange!(1);
      focusStar(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      onChange!(5);
      focusStar(4);
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onChange!(s);
    }
  }

  return (
    <div
      className={`flex gap-1 ${sz}`}
      role="radiogroup"
      aria-label="Оценка от 1 до 5 звёзд"
    >
      {stars.map((s, i) => {
        const filled = s <= value;
        const isFocusable = value === 0 ? s === 1 : s === value;
        return (
          <button
            key={s}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="radio"
            aria-checked={s === value}
            aria-label={`${s} ${s === 1 ? 'звезда' : s < 5 ? 'звезды' : 'звёзд'}`}
            tabIndex={isFocusable ? 0 : -1}
            onClick={() => onChange!(s)}
            onKeyDown={(e) => handleKey(e, s)}
            className={
              filled
                ? 'text-rose hover:scale-110 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-rose rounded-md'
                : 'text-sand hover:scale-110 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-rose rounded-md'
            }
          >
            ★
          </button>
        );
      })}
    </div>
  );
}
