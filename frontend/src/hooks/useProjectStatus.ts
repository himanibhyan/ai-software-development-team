import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type { ProjectStatusResponse } from '@/lib/types';

export function useProjectStatus(projectId: string | undefined) {
  return useQuery({
    queryKey: ['project-status', projectId],
    queryFn: async () => {
      const { data } = await api.get<ProjectStatusResponse>(
        `/projects/${projectId}/status`
      );
      return data;
    },
    enabled: !!projectId,
    refetchInterval: (query) => {
      const state = query.state.data;
      if (!state) return 1000;
      if (state.status === 'running' || state.status === 'pending')
        return 1000;
      return false;
    },
  });
}
