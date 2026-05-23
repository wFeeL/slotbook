import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router';
import { Blob } from '@/shared/ui/Blob';
import { Button } from '@/shared/ui/Button';
import { useHaptic, useMainButton } from '@/shared/telegram/hooks';
import { getWebApp } from '@/shared/telegram/webapp';

export function BookingSuccessPage() {
  const navigate = useNavigate();
  const { bookingId } = useParams();
  const haptic = useHaptic();

  useEffect(() => {
    haptic.success();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleClose() {
    const tg = getWebApp();
    if (tg) {
      tg.close();
    } else {
      navigate('/');
    }
  }

  useMainButton({
    text: 'Закрыть',
    onClick: handleClose,
    visible: true,
  });

  return (
    <div className="relative min-h-screen overflow-hidden flex flex-col items-center justify-center p-6">
      <Blob
        variant="rose"
        size={70}
        className="-top-20 left-1/2 -translate-x-1/2"
        style={{ opacity: 0.18 }}
      />

      <div
        className="relative flex flex-col items-center gap-6 max-w-md text-center"
        style={{ animation: 'fade-up 400ms ease-out both' }}
      >
        <svg width="120" height="120" viewBox="0 0 120 120" aria-hidden>
          <path
            d="M60,8 C84,12 102,32 100,58 C97,82 76,100 50,98 C28,96 12,76 14,52 C16,30 36,12 60,8 Z"
            fill="#8BA888"
            opacity="0.18"
            style={{ animation: 'blob-morph 14s ease-in-out infinite' }}
          />
          <path
            d="M40 62 L54 78 L82 46"
            stroke="#8BA888"
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            strokeDasharray="100"
            strokeDashoffset="100"
            style={{
              animation: 'draw 600ms 200ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
            }}
          />
        </svg>
        <h1 className="text-display text-ink font-display">
          Готово <span className="text-rose">✦</span>
        </h1>
        <p className="text-sienna text-base">
          Запись №{bookingId} подтверждена. Мы напомним вам перед встречей.
        </p>

        {/* Browser preview fallback button — only shown when not inside Telegram */}
        {getWebApp() === null && (
          <Button onClick={handleClose} className="mt-2">
            Закрыть
          </Button>
        )}
      </div>

      <style>{`
        @keyframes draw {
          to { stroke-dashoffset: 0; }
        }
      `}</style>
    </div>
  );
}
