import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '../lib/cn';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'md' | 'lg';
  children: ReactNode;
}

const variantClass = {
  primary:
    'bg-rose text-white shadow-warm hover:bg-rose-deep active:bg-rose-deep',
  secondary: 'bg-shell text-ink border border-sand hover:bg-sand/40 active:bg-sand/60',
  ghost: 'bg-transparent text-ink hover:bg-sand/40 active:bg-sand/60',
};

const sizeClass = {
  md: 'px-5 py-3 text-base rounded-2xl',
  lg: 'px-6 py-4 text-lg rounded-card',
};

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 font-semibold transition active:scale-[0.97]',
        'disabled:opacity-50 disabled:pointer-events-none',
        variantClass[variant],
        sizeClass[size],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
