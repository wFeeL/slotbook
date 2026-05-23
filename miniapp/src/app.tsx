import { lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router';
import { OnboardingPage } from './pages/OnboardingPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { Skeleton } from './shared/ui/Skeleton';

// Lazy-load secondary pages
const BookingFlowPage = lazy(() => import('./pages/BookingFlowPage').then((m) => ({ default: m.BookingFlowPage })));
const BookingSuccessPage = lazy(() => import('./pages/BookingSuccessPage').then((m) => ({ default: m.BookingSuccessPage })));
const MyBookingsPage = lazy(() => import('./pages/MyBookingsPage').then((m) => ({ default: m.MyBookingsPage })));
const BookingDetailPage = lazy(() => import('./pages/BookingDetailPage').then((m) => ({ default: m.BookingDetailPage })));

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
          <Routes>
            <Route path="/" element={<OnboardingPage />} />
            <Route path="/book/success/:bookingId" element={<BookingSuccessPage />} />
            <Route path="/book/*" element={<BookingFlowPage />} />
            <Route path="/my-bookings" element={<MyBookingsPage />} />
            <Route path="/my-bookings/:id" element={<BookingDetailPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
