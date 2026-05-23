import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useStaffForService } from '@/entities/staff/api';
import { StaffCard } from '@/entities/staff/ui/StaffCard';
import { useBookingFlowStore } from '@/shared/store/booking-flow-store';
import { useHaptic, useBackButton } from '@/shared/telegram/hooks';
import { Skeleton } from '@/shared/ui/Skeleton';

export function StaffStep() {
  const navigate = useNavigate();
  const { serviceId, branchId, setStaff } = useBookingFlowStore();
  const haptic = useHaptic();
  const staff = useStaffForService(serviceId, branchId);

  useBackButton(() => navigate('/book/service'));

  useEffect(() => {
    if (serviceId === null) navigate('/book/service', { replace: true });
  }, [serviceId, navigate]);

  function handleSelect(staffId: number) {
    haptic.light();
    setStaff(staffId);
    navigate('/book/date');
  }

  return (
    <div className="px-5 pt-8 pb-32 max-w-md mx-auto" style={{ animation: 'fade-up 320ms ease-out both' }}>
      <header className="mb-6">
        <span className="text-sienna text-sm font-semibold">№ 03</span>
        <h1 className="text-2xl text-ink font-display mt-1">Специалист</h1>
        <p className="text-sienna text-base mt-2">Кто проведёт встречу?</p>
      </header>

      <div className="flex flex-col gap-3">
        {staff.isLoading && (
          <>
            <Skeleton height={80} />
            <Skeleton height={80} />
          </>
        )}
        {staff.error && (
          <div className="rounded-card bg-clay/10 p-4 text-clay text-sm">
            Не удалось загрузить специалистов. Попробуйте позже.
          </div>
        )}
        {staff.data?.map((s) => (
          <StaffCard key={s.id} staff={s} onSelect={() => handleSelect(s.id)} />
        ))}
        {staff.data?.length === 0 && (
          <div className="text-sienna text-center mt-12">
            Нет специалистов, оказывающих эту услугу.
          </div>
        )}
      </div>
    </div>
  );
}
