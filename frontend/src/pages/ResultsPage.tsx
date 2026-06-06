import { useParams, Link } from 'react-router-dom';
import { useProjectDetail } from '@/hooks/useProjectDetail';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { RequirementsView } from '@/components/results/RequirementsView';
import { ArchitectureView } from '@/components/results/ArchitectureView';
import { SourceCodeView } from '@/components/results/SourceCodeView';
import { TestsView } from '@/components/results/TestsView';
import { ReviewView } from '@/components/results/ReviewView';
import { DocumentationView } from '@/components/results/DocumentationView';
import { CheckCircle2, Clock, ArrowLeft, Loader2 } from 'lucide-react';

const TABS = [
  { id: 'requirements', label: 'Requirements' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'source_code', label: 'Source Code' },
  { id: 'test_suite', label: 'Tests' },
  { id: 'review_report', label: 'Review' },
  { id: 'documentation', label: 'Documentation' },
] as const;

export default function ResultsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project, isLoading, error } = useProjectDetail(projectId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-10 w-full max-w-xl" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">
          {error ? 'Failed to load project.' : 'Project not found.'}
        </p>
        <Button asChild variant="link" className="mt-2">
          <Link to="/">Back to Dashboard</Link>
        </Button>
      </div>
    );
  }

  const isActive =
    project.status === 'running' ||
    project.status === 'pending' ||
    project.status === 'refining';

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/history">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {project.idea.length > 80
                ? project.idea.slice(0, 80) + '...'
                : project.idea}
            </h1>
            <p className="text-xs text-muted-foreground font-mono mt-0.5">
              {project.id}
            </p>
          </div>
        </div>
        <Badge
          variant={
            project.status === 'completed'
              ? 'success'
              : project.status === 'failed'
                ? 'destructive'
                : 'info'
          }
        >
          {project.status === 'completed' && (
            <CheckCircle2 className="h-3 w-3 mr-1" />
          )}
          {isActive && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
          {!isActive && project.status !== 'completed' && (
            <Clock className="h-3 w-3 mr-1" />
          )}
          {project.status}
        </Badge>
      </div>

      {isActive && (
        <div className="flex items-center gap-3 text-sm text-muted-foreground bg-muted rounded-lg px-4 py-3">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>
            Generation is still in progress. Not all artifacts are available yet.
          </span>
          <Button variant="outline" size="sm" asChild>
            <Link to={`/projects/${project.id}/monitor`}>
              View Monitor
            </Link>
          </Button>
        </div>
      )}

      {project.status === 'completed' && (
        <Tabs defaultValue="requirements" className="w-full">
          <ScrollArea className="pb-2">
            <TabsList className="inline-flex h-auto p-1 w-max">
              {TABS.map(({ id, label }) => {
                const hasData = project[id as keyof typeof project] != null;
                return (
                  <TabsTrigger
                    key={id}
                    value={id}
                    disabled={!hasData}
                    className="relative"
                  >
                    {label}
                    {hasData ? (
                      <CheckCircle2 className="h-3 w-3 ml-1.5 text-emerald-500" />
                    ) : (
                      <Clock className="h-3 w-3 ml-1.5 text-muted-foreground" />
                    )}
                  </TabsTrigger>
                );
              })}
            </TabsList>
          </ScrollArea>

          <Separator className="my-2" />

          {TABS.map(({ id }) => {
            const artifactData = project[id as keyof typeof project] as
              | Record<string, unknown>
              | undefined;

            if (!artifactData) {
              return (
                <TabsContent key={id} value={id}>
                  <div className="text-center py-12 text-muted-foreground">
                    <Clock className="h-8 w-8 mx-auto mb-2" />
                    <p>This artifact has not been generated yet.</p>
                  </div>
                </TabsContent>
              );
            }

            return (
              <TabsContent key={id} value={id} className="mt-4">
                {id === 'requirements' && (
                  <RequirementsView data={artifactData} />
                )}
                {id === 'architecture' && (
                  <ArchitectureView data={artifactData} />
                )}
                {id === 'source_code' && (
                  <SourceCodeView data={artifactData} />
                )}
                {id === 'test_suite' && <TestsView data={artifactData} />}
                {id === 'review_report' && (
                  <ReviewView data={artifactData} />
                )}
                {id === 'documentation' && (
                  <DocumentationView data={artifactData} />
                )}
              </TabsContent>
            );
          })}
        </Tabs>
      )}

      {project.status === 'failed' && (
        <div className="text-center py-12">
          <p className="text-destructive font-medium">
            Project generation failed.
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            Check the backend logs for details.
          </p>
        </div>
      )}

      <Separator />
      <div className="text-xs text-muted-foreground space-y-0.5">
        <p>Created: {new Date(project.created_at).toLocaleString()}</p>
        <p>Updated: {new Date(project.updated_at).toLocaleString()}</p>
        {project.completed_at && (
          <p>
            Completed: {new Date(project.completed_at).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
}
