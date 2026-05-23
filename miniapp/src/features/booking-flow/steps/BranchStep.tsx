import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useBranches } from '@/entities/branch/api';
import { BranchCard } from '@/entities/branch/ui/BranchCard';
import { Skeleton } from '@/shared/ui/Skeleton';
import { useBookingFlowStore } from '@/shared/store/booking-flow-store';
import { useBackButton, useHaptic } from '@/shared/telegram/hooks';

export function BranchStep() {
  const navigate = useNavigate();
  const q = useBranches();
  const setBranchId = useBookingFlowStore((s) => s.setBranchId);
  const haptic = useHaptic();

  useBackButton(() => navigate('/'));

  // Auto-skip when only one branch
  useEffect(() => {
    if (q.data && q.data.length === 1) {
      setBranchId(q.data[0].id);
      navigate('/book/service', { replace: true });
    }
  }, [q.data, setBranchId, navigate]);

  const branches = q.data ?? [];

  function handleSelect(branchId: number) {
    haptic.light();
    setBranchId(branchId);
    navigate('/book/service');
  }

  return (
    <div
      className="px-5 pt-8 pb-32 max-w-md mx-auto"
      style={{ animation: 'fade-up 320ms ease-out both' }}
    >
      <header className="mb-6">
        <span className="text-sienna text-sm font-semibold">№ 00</span>
        <h1 className="text-2xl text-ink font-display mt-1">Филиал</h1>
        <p className="text-sienna text-base mt-2">Куда вам удобнее?</p>
      </header>

      <div className="flex flex-col gap-3">
        {q.isLoading && (
          <>
            <Skeleton height={90} />
            <Skeleton height={90} />
          </>
        )}
        {q.error && (
          <div className="rounded-card bg-clay/10 p-4 text-clay text-sm">
            Не удалось загрузить филиалы. Попробуйте позже.
          </div>
        )}
        {branches.length > 1 &&
          branches.map((b) => (
            <BranchCard key={b.id} branch={b} onSelect={() => handleSelect(b.id)} />
          ))}
        {!q.isLoading && !q.error && branches.length === 0 && (
          <div className="text-sienna text-center mt-12">Нет доступных филиалов.</div>
        )}
        {/* When exactly 1 branch, the effect auto-navigates — render skeleton while it happens */}
        {branches.length === 1 && <Skeleton height={90} />}
      </div>
    </div>
  );
}
