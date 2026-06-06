import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type { ProjectDetailResponse } from '@/lib/types';

export function useProjectDetail(projectId: string | undefined) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const { data } = await api.get<ProjectDetailResponse>(
        `/projects/${projectId}`
      );
      return data;
    },
    enabled: !!projectId,
    refetchInterval: (query) => {
      const state = query.state.data;
      if (!state) return 2000;
      if (state.status === 'running' || state.status === 'pending')
        return 2000;
      return false;
    },
  });
}
