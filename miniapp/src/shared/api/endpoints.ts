import { request } from './client';
import {
  BookingReadSchema,
  type BookingRead,
  type ServiceRead,
  ServiceReadSchema,
  type SlotsResponse,
  SlotsResponseSchema,
  type StaffRead,
  StaffReadSchema,
  type TelegramAuthResponse,
  TelegramAuthResponseSchema,
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
};
