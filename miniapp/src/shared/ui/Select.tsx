import { useId, type SelectHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../lib/cn';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string | null;
  children: ReactNode;
}

export function Select({ label, error, className, id, children, ...rest }: SelectProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-sienna-deep text-sm font-semibold">
          {label}
        </label>
      )}
      <select
        id={inputId}
        className={cn(
          'rounded-2xl border bg-shell px-4 py-3 text-ink text-base outline-none transition',
          error ? 'border-rose' : 'border-sand focus:border-rose',
          className,
        )}
        {...rest}
      >
        {children}
      </select>
      {error && <span className="text-rose text-xs">{error}</span>}
    </div>
  );
}
