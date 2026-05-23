import { useId, type InputHTMLAttributes } from 'react';
import { cn } from '../lib/cn';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string | null;
}

export function Input({ label, error, className, id, ...rest }: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-sienna-deep text-sm font-semibold">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          'rounded-2xl border bg-shell px-4 py-3 text-ink text-base outline-none transition',
          'placeholder:text-sienna-deep/60',
          error ? 'border-rose' : 'border-sand focus:border-rose',
          className,
        )}
        {...rest}
      />
      {error && <span className="text-rose text-xs">{error}</span>}
    </div>
  );
}
