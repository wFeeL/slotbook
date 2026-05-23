import { lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router';
import { OnboardingPage } from './pages/OnboardingPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { Skeleton } from './shared/ui/Skeleton';
import { ToastContainer } from './shared/ui/Toast';
import { RequireAdmin } from './features/admin-guard/RequireAdmin';
import { AuthGate } from './features/auth/AuthGate';

// Client-side lazy chunks
const BookingFlowPage = lazy(() => import('./pages/BookingFlowPage').then((m) => ({ default: m.BookingFlowPage })));
const BookingSuccessPage = lazy(() => import('./pages/BookingSuccessPage').then((m) => ({ default: m.BookingSuccessPage })));
const MyBookingsPage = lazy(() => import('./pages/MyBookingsPage').then((m) => ({ default: m.MyBookingsPage })));
const BookingDetailPage = lazy(() => import('./pages/BookingDetailPage').then((m) => ({ default: m.BookingDetailPage })));

// Admin chunks (separate so non-admin bundles stay small)
const AdminLayout = lazy(() => import('./pages/admin/AdminLayout').then((m) => ({ default: m.AdminLayout })));
const AdminDashboardPage = lazy(() => import('./pages/admin/AdminDashboardPage').then((m) => ({ default: m.AdminDashboardPage })));
const AdminBookingsPage = lazy(() => import('./pages/admin/AdminBookingsPage').then((m) => ({ default: m.AdminBookingsPage })));
const AdminBookingNewPage = lazy(() => import('./pages/admin/AdminBookingNewPage').then((m) => ({ default: m.AdminBookingNewPage })));
const AdminBookingDetailPage = lazy(() => import('./pages/admin/AdminBookingDetailPage').then((m) => ({ default: m.AdminBookingDetailPage })));
const AdminServicesPage = lazy(() => import('./pages/admin/AdminServicesPage').then((m) => ({ default: m.AdminServicesPage })));
const AdminServiceFormPage = lazy(() => import('./pages/admin/AdminServiceFormPage').then((m) => ({ default: m.AdminServiceFormPage })));
const AdminStaffPage = lazy(() => import('./pages/admin/AdminStaffPage').then((m) => ({ default: m.AdminStaffPage })));
const AdminStaffFormPage = lazy(() => import('./pages/admin/AdminStaffFormPage').then((m) => ({ default: m.AdminStaffFormPage })));
const AdminStaffDetailPage = lazy(() => import('./pages/admin/AdminStaffDetailPage').then((m) => ({ default: m.AdminStaffDetailPage })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function Loading() {
  return (
    <div className="min-h-screen p-6">
      <Skeleton height={48} className="mb-4" />
      <Skeleton height={80} className="mb-3" />
      <Skeleton height={80} />
    </div>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <AuthGate>
            <Routes>
              <Route path="/" element={<OnboardingPage />} />
              <Route path="/book/success/:bookingId" element={<BookingSuccessPage />} />
              <Route path="/book/*" element={<BookingFlowPage />} />
              <Route path="/my-bookings" element={<MyBookingsPage />} />
              <Route path="/my-bookings/:id" element={<BookingDetailPage />} />

              <Route
                path="/admin"
                element={
                  <RequireAdmin>
                    <AdminLayout />
                  </RequireAdmin>
                }
              >
                <Route index element={<AdminDashboardPage />} />
                <Route path="bookings" element={<AdminBookingsPage />} />
                <Route path="bookings/new" element={<AdminBookingNewPage />} />
                <Route path="bookings/:id" element={<AdminBookingDetailPage />} />
                <Route path="services" element={<AdminServicesPage />} />
                <Route path="services/new" element={<AdminServiceFormPage />} />
                <Route path="services/:id/edit" element={<AdminServiceFormPage />} />
                <Route path="staff" element={<AdminStaffPage />} />
                <Route path="staff/new" element={<AdminStaffFormPage />} />
                <Route path="staff/:id" element={<AdminStaffDetailPage />} />
              </Route>

              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </AuthGate>
        </Suspense>
        <ToastContainer />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
