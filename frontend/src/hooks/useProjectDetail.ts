import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type { ProjectDetailResponse } from '@/lib/types';

function shouldRefetch(status: string): boolean {
  return ['running', 'pending', 'refining'].includes(status);
}

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
      if (shouldRefetch(state.status)) return 2000;
      return false;
    },
  });
}
