import { useNavigate } from 'react-router';
import { Button } from '@/shared/ui/Button';

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 p-6">
      <h1 className="text-display text-ink">Здесь пусто</h1>
      <p className="text-sienna-deep">Эта страница не найдена.</p>
      <Button onClick={() => navigate('/')}>На главную</Button>
    </div>
  );
}
