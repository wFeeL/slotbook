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

export const BranchReadSchema = z.object({
  id: z.number(),
  name: z.string(),
  address: z.string().nullable(),
  timezone: z.string(),
  is_active: z.boolean(),
  sort_order: z.number(),
});
export type BranchRead = z.infer<typeof BranchReadSchema>;

export const ServiceReadSchema = z.object({
  id: z.number(),
  branch_id: z.number(),
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
  branch_id: z.number(),
  user_id: z.number().nullable().optional(),
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
  branch_id: z.number(),
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
  branch_id: z.number(),
  client_id: z.number(),
  service_id: z.number(),
  staff_id: z.number(),
  starts_at: z.string(),
  ends_at: z.string(),
  status: BookingStatusSchema,
  client_comment: z.string().nullable(),
  admin_comment: z.string().nullable(),
  service_title: z.string().nullable().optional(),
  staff_name: z.string().nullable().optional(),
  client_first_name: z.string().nullable().optional(),
  client_last_name: z.string().nullable().optional(),
  client_telegram_id: z.number().nullable().optional(),
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
  branch_id: z.number(),
  user_id: z.number().nullable().optional(),
  name: z.string(),
  description: z.string().nullable(),
  is_active: z.boolean(),
  service_ids: z.array(z.number()),
});
export type StaffReadWithServices = z.infer<typeof StaffReadWithServicesSchema>;

export const BusinessReadSchema = z.object({
  id: z.number(),
  name: z.string(),
  timezone: z.string(),
  booking_buffer_minutes: z.number(),
  min_cancellation_hours: z.number(),
  slot_step_minutes: z.number(),
  reminder_long_hours: z.number(),
  reminder_short_hours: z.number(),
});
export type BusinessRead = z.infer<typeof BusinessReadSchema>;

export const MeResponseSchema = z.object({
  id: z.number(),
  telegram_id: z.number(),
  first_name: z.string().nullable(),
  last_name: z.string().nullable(),
  username: z.string().nullable(),
  phone: z.string().nullable(),
  role: UserRoleSchema,
  reminders_enabled: z.boolean(),
});
export type MeResponse = z.infer<typeof MeResponseSchema>;

export const MePreferencesSchema = z.object({
  reminders_enabled: z.boolean(),
});
export type MePreferences = z.infer<typeof MePreferencesSchema>;

export const StatisticsPeriodSchema = z.enum(['7d', '30d', '90d', '365d']);
export type StatisticsPeriodT = z.infer<typeof StatisticsPeriodSchema>;

export const TeamMemberSchema = z.object({
  id: z.number(),
  telegram_id: z.number(),
  first_name: z.string().nullable(),
  last_name: z.string().nullable(),
  username: z.string().nullable(),
  role: z.string(),
  created_at: z.string(),
});
export type TeamMember = z.infer<typeof TeamMemberSchema>;

export const AdminInviteReadSchema = z.object({
  id: z.number(),
  token: z.string(),
  role: z.string(),
  created_at: z.string(),
  expires_at: z.string(),
  url: z.string(),
});
export type AdminInviteRead = z.infer<typeof AdminInviteReadSchema>;

export const TeamResponseSchema = z.object({
  members: z.array(TeamMemberSchema),
  invites: z.array(AdminInviteReadSchema),
});
export type TeamResponse = z.infer<typeof TeamResponseSchema>;

export const StatisticsResponseSchema = z.object({
  period: StatisticsPeriodSchema,
  revenue: z.string(),
  total_bookings: z.number(),
  completed_count: z.number(),
  no_show_count: z.number(),
  cancellation_count: z.number(),
  cancellation_rate: z.number(),
  top_services: z.array(
    z.object({
      service_id: z.number(),
      service_title: z.string(),
      completed_count: z.number(),
      revenue: z.string(),
    }),
  ),
  top_staff: z.array(
    z.object({
      staff_id: z.number(),
      staff_name: z.string(),
      completed_count: z.number(),
    }),
  ),
  daily_volume: z.array(
    z.object({
      date: z.string(),
      bookings_count: z.number(),
    }),
  ),
});
export type StatisticsResponse = z.infer<typeof StatisticsResponseSchema>;

// ---------------------------------------------------------------------------
// Staff cabinet (sub-project 13)
// ---------------------------------------------------------------------------

export const StaffMeStaffSchema = z.object({
  id: z.number(),
  branch_id: z.number(),
  name: z.string(),
  description: z.string().nullable(),
  is_active: z.boolean(),
});
export type StaffMeStaff = z.infer<typeof StaffMeStaffSchema>;

export const StaffMeBranchSchema = z.object({
  id: z.number(),
  name: z.string(),
  timezone: z.string(),
});
export type StaffMeBranch = z.infer<typeof StaffMeBranchSchema>;

export const StaffMeResponseSchema = z.object({
  linked: z.boolean(),
  staff: StaffMeStaffSchema.nullable(),
  branch: StaffMeBranchSchema.nullable(),
  business_timezone: z.string(),
});
export type StaffMeResponse = z.infer<typeof StaffMeResponseSchema>;

export const StaffBookingReadSchema = z.object({
  id: z.number(),
  starts_at: z.string(),
  ends_at: z.string(),
  status: BookingStatusSchema,
  service_id: z.number(),
  service_title: z.string(),
  service_duration_minutes: z.number(),
  service_price: z.string().nullable(),
  client_first_name: z.string().nullable(),
  client_last_name: z.string().nullable(),
  client_phone: z.string().nullable(),
  client_username: z.string().nullable(),
  client_comment: z.string().nullable(),
  admin_comment: z.string().nullable(),
});
export type StaffBookingRead = z.infer<typeof StaffBookingReadSchema>;

export const StaffScheduleIntervalSchema = z.object({
  start_time: z.string(),
  end_time: z.string(),
});
export const StaffScheduleExceptionSchema = z.object({
  id: z.number(),
  date: z.string(),
  type: z.enum(['day_off', 'extra_working_time', 'blocked_time']),
  start_time: z.string().nullable(),
  end_time: z.string().nullable(),
  reason: z.string().nullable(),
});
export const StaffScheduleBookingSchema = z.object({
  id: z.number(),
  starts_at: z.string(),
  ends_at: z.string(),
  service_title: z.string(),
  client_first_name: z.string().nullable(),
  status: BookingStatusSchema,
});
export const StaffScheduleDaySchema = z.object({
  date: z.string(),
  weekday: z.number(),
  working_intervals: z.array(StaffScheduleIntervalSchema),
  exceptions: z.array(StaffScheduleExceptionSchema),
  bookings: z.array(StaffScheduleBookingSchema),
});
export const StaffScheduleResponseSchema = z.object({
  week_start: z.string(),
  business_timezone: z.string(),
  days: z.array(StaffScheduleDaySchema),
});
export type StaffScheduleResponse = z.infer<typeof StaffScheduleResponseSchema>;
export type StaffScheduleDay = z.infer<typeof StaffScheduleDaySchema>;

export const UserBriefSchema = z.object({
  id: z.number(),
  telegram_id: z.number(),
  first_name: z.string().nullable(),
  last_name: z.string().nullable(),
  username: z.string().nullable(),
  role: UserRoleSchema,
});
export type UserBrief = z.infer<typeof UserBriefSchema>;
