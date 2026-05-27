// miniapp/src/pages/admin/AdminLayout.tsx
import type { ReactElement, SVGProps } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router';
import { Badge } from '@/shared/ui/Badge';
import { useBackButton } from '@/shared/telegram/hooks';
import { cn } from '@/shared/lib/cn';

type IconComponent = (props: SVGProps<SVGSVGElement>) => ReactElement;

const iconBaseProps = {
  width: 22,
  height: 22,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

const HomeIcon: IconComponent = (props) => (
  <svg {...iconBaseProps} {...props}>
    <path d="M3 10.5 12 3l9 7.5V20a1.5 1.5 0 0 1-1.5 1.5h-3.75v-7h-5.5v7H4.5A1.5 1.5 0 0 1 3 20z" />
  </svg>
);

const CalendarIcon: IconComponent = (props) => (
  <svg {...iconBaseProps} {...props}>
    <rect x="3.25" y="4.5" width="17.5" height="16" rx="2.5" />
    <path d="M8 3v3M16 3v3M3.25 9.5h17.5" />
  </svg>
);

const ListIcon: IconComponent = (props) => (
  <svg {...iconBaseProps} {...props}>
    <path d="M8 6h12M8 12h12M8 18h12" />
    <circle cx="4" cy="6" r="1" />
    <circle cx="4" cy="12" r="1" />
    <circle cx="4" cy="18" r="1" />
  </svg>
);

const SparkleIcon: IconComponent = (props) => (
  <svg {...iconBaseProps} {...props}>
    <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.5 5.5l2.8 2.8M15.7 15.7l2.8 2.8M5.5 18.5l2.8-2.8M15.7 8.3l2.8-2.8" />
  </svg>
);

const UsersIcon: IconComponent = (props) => (
  <svg {...iconBaseProps} {...props}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="3.5" />
    <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.5a4 4 0 0 1 0 7.5" />
  </svg>
);

interface NavItem {
  to: string;
  label: string;
  Icon: IconComponent;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/admin', label: 'Главная', Icon: HomeIcon, end: true },
  { to: '/admin/calendar', label: 'Календарь', Icon: CalendarIcon },
  { to: '/admin/bookings', label: 'Записи', Icon: ListIcon },
  { to: '/admin/services', label: 'Услуги', Icon: SparkleIcon },
  { to: '/admin/staff', label: 'Сотрудники', Icon: UsersIcon },
  { to: '/admin/reviews', label: 'Отзывы', Icon: SparkleIcon },
];

export function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  // Telegram BackButton: on nested /admin/* pages → back to /admin.
  // Only from /admin root → back to /.
  useBackButton(() => {
    if (location.pathname === '/admin' || location.pathname === '/admin/') {
      navigate('/');
    } else {
      navigate('/admin');
    }
  });

  return (
    <div className="min-h-screen pb-24 bg-cream">
      <header className="px-5 pt-6 pb-3 flex items-center justify-between">
        <h1 className="text-2xl text-ink font-display">SlotBook</h1>
        <Badge tone="sienna">Админ</Badge>
      </header>

      <main className="px-5">
        <Outlet />
      </main>

      <nav
        className="fixed bottom-0 left-0 right-0 z-40 bg-shell border-t border-sand"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <ul className="flex items-stretch justify-around max-w-md mx-auto">
          {NAV_ITEMS.map((item) => (
            <li key={item.to} className="flex-1">
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    'flex flex-col items-center gap-1 py-2.5 transition',
                    isActive ? 'text-rose' : 'text-sienna-deep',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <item.Icon
                      className={cn('transition-transform', isActive && 'scale-110')}
                    />
                    <span className="text-[11px] font-semibold">{item.label}</span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
