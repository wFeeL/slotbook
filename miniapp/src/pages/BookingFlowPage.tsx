import { Navigate, Route, Routes } from 'react-router';
import { BranchStep } from '@/features/booking-flow/steps/BranchStep';
import { ServiceStep } from '@/features/booking-flow/steps/ServiceStep';
import { StaffStep } from '@/features/booking-flow/steps/StaffStep';
import { DateStep } from '@/features/booking-flow/steps/DateStep';
import { TimeStep } from '@/features/booking-flow/steps/TimeStep';
import { ConfirmStep } from '@/features/booking-flow/steps/ConfirmStep';

export function BookingFlowPage() {
  return (
    <Routes>
      <Route index element={<Navigate to="branch" replace />} />
      <Route path="branch" element={<BranchStep />} />
      <Route path="service" element={<ServiceStep />} />
      <Route path="staff" element={<StaffStep />} />
      <Route path="date" element={<DateStep />} />
      <Route path="time" element={<TimeStep />} />
      <Route path="confirm" element={<ConfirmStep />} />
    </Routes>
  );
}
