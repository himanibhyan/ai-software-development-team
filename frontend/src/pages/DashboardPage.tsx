import { useState } from 'react';
import { useCreateProject } from '@/hooks/useCreateProject';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Sparkles, Loader2 } from 'lucide-react';

export default function DashboardPage() {
  const [idea, setIdea] = useState('');
  const [constraintsText, setConstraintsText] = useState('');

  const mutation = useCreateProject();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!idea.trim()) return;

    let constraints: Record<string, unknown> | undefined;
    if (constraintsText.trim()) {
      try {
        constraints = JSON.parse(constraintsText.trim());
      } catch {
        return;
      }
    }

    mutation.mutate({ idea: idea.trim(), constraints });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Generate a Software Project
        </h1>
        <p className="text-muted-foreground mt-2">
          Describe your software idea and let the AI development team build it
          for you.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Idea</CardTitle>
            <CardDescription>
              Describe the software you want to build in natural language (at
              least 10 characters).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="A microservice-based task management system with real-time collaboration..."
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              rows={6}
              className="resize-y min-h-[140px]"
            />
            {mutation.isError && (
              <p className="text-sm text-destructive mt-2">
                {mutation.error?.message || 'Failed to create project'}
              </p>
            )}
            {mutation.data && (
              <p className="text-sm text-emerald-500 mt-2">
                Project created! Redirecting to monitor...
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Constraints (optional)</CardTitle>
            <CardDescription>
              Specify tech stack, preferences, or any constraints as JSON.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder='{"tech_stack": "Python, FastAPI, PostgreSQL", "ui_framework": "React"}'
              value={constraintsText}
              onChange={(e) => setConstraintsText(e.target.value)}
              rows={4}
              className="resize-y font-mono text-sm"
            />
            {constraintsText.trim() && (
              (() => {
                try {
                  JSON.parse(constraintsText.trim());
                  return (
                    <p className="text-xs text-emerald-500 mt-1">
                      Valid JSON
                    </p>
                  );
                } catch {
                  return (
                    <p className="text-xs text-destructive mt-1">
                      Invalid JSON
                    </p>
                  );
                }
              })()
            )}
          </CardContent>
        </Card>

        <Button
          type="submit"
          size="lg"
          className="w-full gap-2"
          disabled={mutation.isPending || idea.trim().length < 10}
        >
          {mutation.isPending ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Sparkles className="h-5 w-5" />
          )}
          {mutation.isPending ? 'Generating...' : 'Generate Project'}
        </Button>
      </form>
    </div>
  );
}
