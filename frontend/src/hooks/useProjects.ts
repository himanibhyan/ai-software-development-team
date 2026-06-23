import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type {
  PaginatedResponse,
  ProjectSummaryResponse,
} from '@/lib/types';

interface UseProjectsParams {
  page?: number;
  pageSize?: number;
  status?: string;
}

export function useProjects(params: UseProjectsParams = {}) {
  const { page = 1, pageSize = 20, status } = params;

  return useQuery({
    queryKey: ['projects', { page, pageSize, status }],
    queryFn: async () => {
      const queryParams: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (status) {
        queryParams.status = status;
      }
      const { data } = await api.get<PaginatedResponse<ProjectSummaryResponse>>(
        '/projects',
        { params: queryParams }
      );
      return data;
    },
    placeholderData: (previousData) => previousData,
  });
}
