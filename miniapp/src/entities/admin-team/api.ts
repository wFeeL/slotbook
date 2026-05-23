import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/api/endpoints';
import { adminTeamKeys } from './model';

export function useTeam() {
  return useQuery({
    queryKey: adminTeamKeys.root(),
    queryFn: () => api.admin.team.get(),
    staleTime: 30 * 1000,
  });
}

export function useCreateInvite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.team.createInvite,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminTeamKeys.root() }),
  });
}

export function useRevokeInvite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.admin.team.revokeInvite,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminTeamKeys.root() }),
  });
}
