import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useProjects } from '@/hooks/useProjects';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Eye,
  CheckCircle2,
  Loader2,
  XCircle,
  Clock,
  FileText,
  Sparkles,
} from 'lucide-react';

const statusConfig: Record<
  string,
  { variant: 'success' | 'destructive' | 'warning' | 'info' | 'secondary'; icon: React.ReactNode }
> = {
  completed: {
    variant: 'success',
    icon: <CheckCircle2 className="h-3 w-3 mr-1" />,
  },
  running: {
    variant: 'info',
    icon: <Loader2 className="h-3 w-3 mr-1 animate-spin" />,
  },
  refining: {
    variant: 'info',
    icon: <Loader2 className="h-3 w-3 mr-1 animate-spin" />,
  },
  pending: {
    variant: 'warning',
    icon: <Clock className="h-3 w-3 mr-1" />,
  },
  failed: {
    variant: 'destructive',
    icon: <XCircle className="h-3 w-3 mr-1" />,
  },
};

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading, error } = useProjects({
    page,
    pageSize: 20,
    status: statusFilter || undefined,
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Project History
          </h1>
          <p className="text-muted-foreground mt-1">
            Browse all previously generated projects.
          </p>
        </div>
        <Button asChild>
          <Link to="/">
            <Sparkles className="h-4 w-4 mr-1" /> New Project
          </Link>
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <Select
          value={statusFilter || 'all'}
          onValueChange={(v) => {
            setStatusFilter(v === 'all' ? '' : v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="refining">Refining</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <p className="text-destructive">Failed to load projects.</p>
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="text-center py-20">
          <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">No projects found.</p>
          <Button asChild variant="link" className="mt-2">
            <Link to="/">Create your first project</Link>
          </Button>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-3">
          {data.items.map((project) => {
            const cfg =
              statusConfig[project.status] ?? statusConfig.pending;
            return (
              <Card key={project.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1 min-w-0">
                      <CardTitle className="text-base truncate">
                        {project.idea}
                      </CardTitle>
                      <p className="text-xs text-muted-foreground font-mono">
                        {project.id}
                      </p>
                    </div>
                    <Badge variant={cfg.variant as 'success' | 'destructive' | 'warning' | 'info' | 'secondary'}>
                      {cfg.icon}
                      {project.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4 text-muted-foreground">
                      <span>
                        Created:{' '}
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                      {project.artifact_count > 0 && (
                        <span>
                          {project.artifact_count} artifact
                          {project.artifact_count !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <Link to={`/projects/${project.id}`}>
                        <Eye className="h-3 w-3 mr-1" /> Open
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {data.page} of {data.total_pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= data.total_pages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
