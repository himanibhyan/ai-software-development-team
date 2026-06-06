export interface CreateProjectRequest {
  idea: string;
  constraints?: Record<string, unknown>;
}

export interface RefineProjectRequest {
  feedback: string;
  target_agents?: string[];
}

export interface CreateProjectResponse {
  project_id: string;
  status: string;
  status_url: string;
}

export interface ProjectSummaryResponse {
  id: string;
  idea: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  artifact_count: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProjectDetailResponse {
  id: string;
  idea: string;
  constraints?: Record<string, unknown>;
  status: ProjectStatus;
  requirements?: Record<string, unknown>;
  architecture?: Record<string, unknown>;
  source_code?: Record<string, unknown>;
  test_suite?: Record<string, unknown>;
  documentation?: Record<string, unknown>;
  review_report?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ProjectStatusResponse {
  project_id: string;
  status: ProjectStatus;
  idea: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type ProjectStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'refining';

export type AgentType =
  | 'requirements'
  | 'architect'
  | 'developer'
  | 'tester'
  | 'code_review'
  | 'documentation'
  | 'orchestrator';

export const AGENT_LABELS: Record<AgentType, string> = {
  requirements: 'Requirements Analyst',
  architect: 'Software Architect',
  developer: 'Developer',
  tester: 'QA Tester',
  code_review: 'Code Reviewer',
  documentation: 'Technical Writer',
  orchestrator: 'Orchestrator',
};

export const AGENT_ORDER: AgentType[] = [
  'requirements',
  'architect',
  'developer',
  'code_review',
  'tester',
  'documentation',
];

export const STATUS_ORDER: Record<ProjectStatus, number> = {
  pending: 0,
  running: 1,
  refining: 1,
  completed: 2,
  failed: 2,
};
