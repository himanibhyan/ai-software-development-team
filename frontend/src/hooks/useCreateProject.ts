import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import type {
  CreateProjectRequest,
  CreateProjectResponse,
} from '@/lib/types';

export function useCreateProject() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (req: CreateProjectRequest) => {
      const { data } = await api.post<CreateProjectResponse>(
        '/projects',
        req
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      navigate(`/projects/${data.project_id}/monitor`);
    },
  });
}
