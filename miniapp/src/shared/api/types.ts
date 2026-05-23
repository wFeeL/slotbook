import { z } from 'zod';

export const UserRoleSchema = z.enum(['client', 'admin', 'staff', 'superadmin']);
export type UserRole = z.infer<typeof UserRoleSchema>;

export const UserReadSchema = z.object({
  id: z.number(),
  telegram_id: z.number(),
  first_name: z.string().nullable(),
  last_name: z.string().nullable(),
  username: z.string().nullable(),
  role: UserRoleSchema,
});
export type UserRead = z.infer<typeof UserReadSchema>;

export const TelegramAuthResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
  expires_in: z.number(),
  user: UserReadSchema,
});
export type TelegramAuthResponse = z.infer<typeof TelegramAuthResponseSchema>;

export const ServiceReadSchema = z.object({
  id: z.number(),
  title: z.string(),
  description: z.string().nullable(),
  duration_minutes: z.number(),
  price: z.string().nullable(),
  is_active: z.boolean(),
  sort_order: z.number(),
});
export type ServiceRead = z.infer<typeof ServiceReadSchema>;

export const StaffReadSchema = z.object({
  id: z.number(),
  name: z.string(),
  description: z.string().nullable(),
  is_active: z.boolean(),
});
export type StaffRead = z.infer<typeof StaffReadSchema>;

export const SlotReadSchema = z.object({
  starts_at: z.string(),
  ends_at: z.string(),
  starts_at_local: z.string(),
  ends_at_local: z.string(),
});
export type SlotRead = z.infer<typeof SlotReadSchema>;

export const SlotsResponseSchema = z.object({
  date: z.string(),
  timezone: z.string(),
  slots: z.array(SlotReadSchema),
});
export type SlotsResponse = z.infer<typeof SlotsResponseSchema>;

export const BookingStatusSchema = z.enum([
  'pending',
  'confirmed',
  'cancelled_by_client',
  'cancelled_by_admin',
  'completed',
  'no_show',
  'rescheduled',
]);
export type BookingStatus = z.infer<typeof BookingStatusSchema>;

export const BookingReadSchema = z.object({
  id: z.number(),
  service_id: z.number(),
  staff_id: z.number(),
  starts_at: z.string(),
  ends_at: z.string(),
  status: BookingStatusSchema,
  client_comment: z.string().nullable(),
});
export type BookingRead = z.infer<typeof BookingReadSchema>;

export const ErrorDetailSchema = z.object({
  code: z.string(),
  message: z.string(),
  extra: z.record(z.unknown()).optional(),
});

// ---------------------------------------------------------------------------
// Admin schemas
// ---------------------------------------------------------------------------

export const AdminBookingReadSchema = z.object({
  id: z.number(),
  client_id: z.number(),
  service_id: z.number(),
  staff_id: z.number(),
  starts_at: z.string(),
  ends_at: z.string(),
  status: BookingStatusSchema,
  client_comment: z.string().nullable(),
  admin_comment: z.string().nullable(),
});
export type AdminBookingRead = z.infer<typeof AdminBookingReadSchema>;

export const ScheduleExceptionTypeSchema = z.enum(['day_off', 'extra_working_time', 'blocked_time']);
export type ScheduleExceptionTypeT = z.infer<typeof ScheduleExceptionTypeSchema>;

export const WorkingHoursEntrySchema = z.object({
  weekday: z.number().int().min(0).max(6),
  start_time: z.string(),
  end_time: z.string(),
  is_active: z.boolean(),
});
export type WorkingHoursEntry = z.infer<typeof WorkingHoursEntrySchema>;

export const ScheduleExceptionReadSchema = z.object({
  id: z.number(),
  date: z.string(),
  start_time: z.string().nullable(),
  end_time: z.string().nullable(),
  type: ScheduleExceptionTypeSchema,
  reason: z.string().nullable(),
});
export type ScheduleExceptionRead = z.infer<typeof ScheduleExceptionReadSchema>;

export const DashboardCountsSchema = z.object({
  today: z.number(),
  this_week: z.number(),
  no_show_30d: z.number(),
});
export type DashboardCounts = z.infer<typeof DashboardCountsSchema>;

export const DashboardResponseSchema = z.object({
  counts: DashboardCountsSchema,
});
export type DashboardResponse = z.infer<typeof DashboardResponseSchema>;

export const StaffReadWithServicesSchema = z.object({
  id: z.number(),
  name: z.string(),
  description: z.string().nullable(),
  is_active: z.boolean(),
  service_ids: z.array(z.number()),
});
export type StaffReadWithServices = z.infer<typeof StaffReadWithServicesSchema>;
