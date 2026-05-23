import { useId, type TextareaHTMLAttributes } from 'react';
import { cn } from '../lib/cn';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string | null;
}

export function Textarea({ label, error, className, id, ...rest }: TextareaProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-sienna text-sm font-semibold">
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        rows={3}
        className={cn(
          'rounded-2xl border bg-shell px-4 py-3 text-ink text-base outline-none transition resize-none',
          'placeholder:text-sienna/60',
          error ? 'border-rose' : 'border-sand focus:border-rose',
          className,
        )}
        {...rest}
      />
      {error && <span className="text-rose text-xs">{error}</span>}
    </div>
  );
}
