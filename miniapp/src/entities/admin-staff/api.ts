import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { adminStaffKeys } from './model';

export function useAdminStaff() {
  // Aggregate staff across all services. Backend doesn't have an "all staff"
  // endpoint, but the public endpoint accepts service_id. We fetch services
  // and union staff per service.
  return useQuery({
    queryKey: adminStaffKeys.list(),
    queryFn: async () => {
      const services = await api.services.list();
      const seen = new Map<number, Awaited<ReturnType<typeof api.staff.listForService>>[number]>();
      for (const s of services) {
        const list = await api.staff.listForService(s.id);
        for (const st of list) seen.set(st.id, st);
      }
      return Array.from(seen.values());
    },
    staleTime: 30 * 1000,
  });
}

export function useStaffWorkingHours(staffId: number, enabled = true) {
  return useQuery({
    queryKey: adminStaffKeys.workingHours(staffId),
    queryFn: () => api.admin.staff.getWorkingHours(staffId),
    enabled,
    staleTime: 30 * 1000,
  });
}

export function useCreateStaff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.staff.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminStaffKeys.list() }),
  });
}

export function useUpdateStaff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Parameters<typeof api.admin.staff.update>[1] }) =>
      api.admin.staff.update(id, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: adminStaffKeys.list() }),
  });
}

export function useArchiveStaff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.staff.archive,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminStaffKeys.list() }),
  });
}

export function useReplaceStaffServices() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, serviceIds }: { id: number; serviceIds: number[] }) =>
      api.admin.staff.replaceServices(id, serviceIds),
    onSuccess: (_data, vars) =>
      qc.invalidateQueries({ queryKey: adminStaffKeys.detail(vars.id) }),
  });
}

export function useReplaceWorkingHours() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      entries,
    }: {
      id: number;
      entries: Parameters<typeof api.admin.staff.replaceWorkingHours>[1];
    }) => api.admin.staff.replaceWorkingHours(id, entries),
    onSuccess: (_d, vars) =>
      qc.invalidateQueries({ queryKey: adminStaffKeys.workingHours(vars.id) }),
  });
}

export function useCreateException() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      staffId,
      body,
    }: {
      staffId: number;
      body: Parameters<typeof api.admin.staff.createException>[1];
    }) => api.admin.staff.createException(staffId, body),
    onSuccess: (_d, vars) =>
      qc.invalidateQueries({ queryKey: adminStaffKeys.detail(vars.staffId) }),
  });
}

export function useDeleteException() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ staffId, exceptionId }: { staffId: number; exceptionId: number }) =>
      api.admin.staff.deleteException(staffId, exceptionId),
    onSuccess: (_d, vars) =>
      qc.invalidateQueries({ queryKey: adminStaffKeys.detail(vars.staffId) }),
  });
}
