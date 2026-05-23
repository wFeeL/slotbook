import { useNavigate } from 'react-router';
import { useServices } from '@/entities/service/api';
import { ServiceCard } from '@/entities/service/ui/ServiceCard';
import { useBookingFlowStore } from '@/shared/store/booking-flow-store';
import { useHaptic, useBackButton } from '@/shared/telegram/hooks';
import { Skeleton } from '@/shared/ui/Skeleton';

export function ServiceStep() {
  const navigate = useNavigate();
  const setService = useBookingFlowStore((s) => s.setService);
  const branchId = useBookingFlowStore((s) => s.branchId);
  const haptic = useHaptic();
  const services = useServices({ branchId });

  useBackButton(() => navigate('/book/branch'));

  function handleSelect(serviceId: number) {
    haptic.light();
    setService(serviceId);
    navigate('/book/staff');
  }

  return (
    <div className="px-5 pt-8 pb-32 max-w-md mx-auto" style={{ animation: 'fade-up 320ms ease-out both' }}>
      <header className="mb-6">
        <span className="text-sienna text-sm font-semibold">№ 02</span>
        <h1 className="text-2xl text-ink font-display mt-1">Услуга</h1>
        <p className="text-sienna text-base mt-2">Что вас сегодня интересует?</p>
      </header>

      <div className="flex flex-col gap-3">
        {services.isLoading && (
          <>
            <Skeleton height={90} />
            <Skeleton height={90} />
            <Skeleton height={90} />
          </>
        )}
        {services.error && (
          <div className="rounded-card bg-clay/10 p-4 text-clay text-sm">
            Не удалось загрузить услуги. Попробуйте позже.
          </div>
        )}
        {services.data?.map((service) => (
          <ServiceCard key={service.id} service={service} onSelect={() => handleSelect(service.id)} />
        ))}
        {services.data?.length === 0 && (
          <div className="text-sienna text-center mt-12">Услуги пока не настроены.</div>
        )}
      </div>
    </div>
  );
}
