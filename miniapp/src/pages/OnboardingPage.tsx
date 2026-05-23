import { useNavigate } from 'react-router';
import { Blob } from '@/shared/ui/Blob';
import { Button } from '@/shared/ui/Button';
import { useAuth } from '@/features/auth/useAuth';
import { useAuthStore } from '@/shared/store/auth-store';

export function OnboardingPage() {
  const navigate = useNavigate();
  const { firstName } = useAuth();
  const role = useAuthStore((s) => s.user?.role);
  const isAdmin = role === 'admin' || role === 'superadmin';
  const businessName = import.meta.env.VITE_BUSINESS_NAME ?? 'SlotBook';

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blob variant="sand" size={70} className="-top-32 -right-20" />
      <Blob variant="rose" size={50} className="-bottom-24 -left-16" style={{ opacity: 0.3 }} />

      <div className="relative px-5 pt-12 pb-8 max-w-md mx-auto flex flex-col gap-10">
        <header
          className="flex flex-col gap-2"
          style={{ animation: 'fade-up 320ms ease-out both' }}
        >
          <span className="text-sienna text-sm font-semibold tracking-wide uppercase">
            {businessName}
          </span>
          <h1 className="text-display text-ink font-display leading-tight">
            Привет, {firstName ?? 'друг'} <span className="text-rose">✦</span>
          </h1>
          <p className="text-sienna text-base">
            Здесь живёт ваша запись.<br />Тихая и заботливая.
          </p>
        </header>

        <div className="flex flex-col gap-4" style={{ animation: 'fade-up 320ms 80ms ease-out both' }}>
          <Button size="lg" onClick={() => navigate('/book/service')}>
            <span className="flex flex-col items-start gap-0.5 text-left">
              <span>Записаться</span>
              <span className="text-sm font-normal opacity-80">новая встреча</span>
            </span>
          </Button>
          <Button size="lg" variant="secondary" onClick={() => navigate('/my-bookings')}>
            <span className="flex flex-col items-start gap-0.5 text-left">
              <span>Мои записи</span>
              <span className="text-sm font-normal opacity-80">история и предстоящее</span>
            </span>
          </Button>
          {isAdmin && (
            <Button size="lg" variant="ghost" onClick={() => navigate('/admin')}>
              <span className="flex flex-col items-start gap-0.5 text-left">
                <span>Панель администратора</span>
                <span className="text-sm font-normal opacity-80">управление бизнесом</span>
              </span>
            </Button>
          )}
        </div>

        <footer
          className="text-center text-sienna text-xs mt-auto"
          style={{ animation: 'fade-up 320ms 160ms ease-out both' }}
        >
          <span>✦ {businessName} ✦</span>
        </footer>
      </div>
    </div>
  );
}
