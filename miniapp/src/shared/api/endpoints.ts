import { request } from './client';
import {
  AdminBookingReadSchema,
  type AdminBookingRead,
  BookingReadSchema,
  type BookingRead,
  DashboardResponseSchema,
  type DashboardResponse,
  ScheduleExceptionReadSchema,
  type ScheduleExceptionRead,
  type ServiceRead,
  ServiceReadSchema,
  type SlotsResponse,
  SlotsResponseSchema,
  type StaffRead,
  StaffReadSchema,
  type TelegramAuthResponse,
  TelegramAuthResponseSchema,
  WorkingHoursEntrySchema,
  type WorkingHoursEntry,
} from './types';
import { z } from 'zod';

export const api = {
  auth: {
    telegram(initData: string): Promise<TelegramAuthResponse> {
      return request(
        '/api/v1/auth/telegram',
        { method: 'POST', body: JSON.stringify({ init_data: initData }) },
        TelegramAuthResponseSchema,
      );
    },
  },
  services: {
    list(): Promise<ServiceRead[]> {
      return request('/api/v1/services', { method: 'GET' }, z.array(ServiceReadSchema));
    },
  },
  staff: {
    listForService(serviceId: number): Promise<StaffRead[]> {
      const params = new URLSearchParams({ service_id: String(serviceId) });
      return request(`/api/v1/staff?${params}`, { method: 'GET' }, z.array(StaffReadSchema));
    },
  },
  slots: {
    forDay(args: { serviceId: number; staffId: number; date: string }): Promise<SlotsResponse> {
      const params = new URLSearchParams({
        service_id: String(args.serviceId),
        staff_id: String(args.staffId),
        date: args.date,
      });
      return request(`/api/v1/slots?${params}`, { method: 'GET' }, SlotsResponseSchema);
    },
  },
  bookings: {
    create(args: {
      service_id: number;
      staff_id: number;
      starts_at: string;
      client_comment?: string | null;
    }): Promise<BookingRead> {
      return request(
        '/api/v1/bookings',
        { method: 'POST', body: JSON.stringify(args) },
        BookingReadSchema,
      );
    },
    listMy(): Promise<BookingRead[]> {
      return request('/api/v1/bookings/my', { method: 'GET' }, z.array(BookingReadSchema));
    },
    cancel(bookingId: number): Promise<BookingRead> {
      return request(`/api/v1/bookings/${bookingId}/cancel`, { method: 'POST' }, BookingReadSchema);
    },
  },
  admin: {
    dashboard(): Promise<DashboardResponse> {
      return request('/api/v1/admin/dashboard', { method: 'GET' }, DashboardResponseSchema);
    },
    services: {
      create(body: {
        title: string;
        description?: string | null;
        duration_minutes: number;
        price?: string | null;
        sort_order?: number;
      }): Promise<ServiceRead> {
        return request(
          '/api/v1/admin/services',
          { method: 'POST', body: JSON.stringify(body) },
          ServiceReadSchema,
        );
      },
      update(
        id: number,
        body: Partial<{
          title: string;
          description: string | null;
          duration_minutes: number;
          price: string | null;
          sort_order: number;
          is_active: boolean;
        }>,
      ): Promise<ServiceRead> {
        return request(
          `/api/v1/admin/services/${id}`,
          { method: 'PATCH', body: JSON.stringify(body) },
          ServiceReadSchema,
        );
      },
      archive(id: number): Promise<void> {
        return request(`/api/v1/admin/services/${id}`, { method: 'DELETE' }, z.unknown()).then(
          () => undefined,
        );
      },
    },
    staff: {
      create(body: { name: string; description?: string | null }): Promise<StaffRead> {
        return request(
          '/api/v1/admin/staff',
          { method: 'POST', body: JSON.stringify(body) },
          StaffReadSchema,
        );
      },
      update(
        id: number,
        body: Partial<{ name: string; description: string | null; is_active: boolean }>,
      ): Promise<StaffRead> {
        return request(
          `/api/v1/admin/staff/${id}`,
          { method: 'PATCH', body: JSON.stringify(body) },
          StaffReadSchema,
        );
      },
      archive(id: number): Promise<void> {
        return request(`/api/v1/admin/staff/${id}`, { method: 'DELETE' }, z.unknown()).then(
          () => undefined,
        );
      },
      replaceServices(id: number, serviceIds: number[]): Promise<void> {
        return request(
          `/api/v1/admin/staff/${id}/services`,
          { method: 'PUT', body: JSON.stringify({ service_ids: serviceIds }) },
          z.unknown(),
        ).then(() => undefined);
      },
      getWorkingHours(id: number): Promise<WorkingHoursEntry[]> {
        return request(
          `/api/v1/admin/staff/${id}/working-hours`,
          { method: 'GET' },
          z.array(WorkingHoursEntrySchema),
        );
      },
      replaceWorkingHours(id: number, entries: WorkingHoursEntry[]): Promise<void> {
        return request(
          `/api/v1/admin/staff/${id}/working-hours`,
          { method: 'PUT', body: JSON.stringify({ entries }) },
          z.unknown(),
        ).then(() => undefined);
      },
      createException(
        staffId: number,
        body: {
          date: string;
          type: 'day_off' | 'extra_working_time' | 'blocked_time';
          start_time?: string | null;
          end_time?: string | null;
          reason?: string | null;
        },
      ): Promise<ScheduleExceptionRead> {
        return request(
          `/api/v1/admin/staff/${staffId}/exceptions`,
          { method: 'POST', body: JSON.stringify(body) },
          ScheduleExceptionReadSchema,
        );
      },
      deleteException(staffId: number, exceptionId: number): Promise<void> {
        return request(
          `/api/v1/admin/staff/${staffId}/exceptions/${exceptionId}`,
          { method: 'DELETE' },
          z.unknown(),
        ).then(() => undefined);
      },
    },
    bookings: {
      list(params: {
        date?: string;
        staff_id?: number;
        service_id?: number;
        status?: string;
        limit?: number;
        offset?: number;
      }): Promise<AdminBookingRead[]> {
        const search = new URLSearchParams();
        if (params.date) search.set('date', params.date);
        if (params.staff_id !== undefined) search.set('staff_id', String(params.staff_id));
        if (params.service_id !== undefined) search.set('service_id', String(params.service_id));
        if (params.status) search.set('status', params.status);
        if (params.limit !== undefined) search.set('limit', String(params.limit));
        if (params.offset !== undefined) search.set('offset', String(params.offset));
        const qs = search.toString();
        return request(
          `/api/v1/admin/bookings${qs ? `?${qs}` : ''}`,
          { method: 'GET' },
          z.array(AdminBookingReadSchema),
        );
      },
      patch(
        id: number,
        body: { admin_comment?: string | null; status?: 'completed' | 'no_show' },
      ): Promise<AdminBookingRead> {
        return request(
          `/api/v1/admin/bookings/${id}`,
          { method: 'PATCH', body: JSON.stringify(body) },
          AdminBookingReadSchema,
        );
      },
      create(body: {
        client_telegram_id: number;
        service_id: number;
        staff_id: number;
        starts_at: string;
        client_comment?: string | null;
        admin_comment?: string | null;
      }): Promise<AdminBookingRead> {
        return request(
          '/api/v1/admin/bookings',
          { method: 'POST', body: JSON.stringify(body) },
          AdminBookingReadSchema,
        );
      },
      cancel(id: number): Promise<AdminBookingRead> {
        return request(
          `/api/v1/admin/bookings/${id}/cancel`,
          { method: 'POST' },
          AdminBookingReadSchema,
        );
      },
    },
  },
};
