// miniapp/src/pages/admin/AdminLayout.tsx
import { Outlet, NavLink, useNavigate } from 'react-router';
import { Badge } from '@/shared/ui/Badge';
import { useBackButton } from '@/shared/telegram/hooks';
import { cn } from '@/shared/lib/cn';

interface NavItem {
  to: string;
  label: string;
  icon: string;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/admin', label: 'Главная', icon: '✦', end: true },
  { to: '/admin/bookings', label: 'Записи', icon: '◷' },
  { to: '/admin/services', label: 'Услуги', icon: '✤' },
  { to: '/admin/staff', label: 'Сотрудники', icon: '☺' },
];

export function AdminLayout() {
  const navigate = useNavigate();
  useBackButton(() => navigate('/'));

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
                    isActive ? 'text-rose' : 'text-sienna',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <span className={cn('text-xl transition-transform', isActive && 'scale-110')}>
                      {item.icon}
                    </span>
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
