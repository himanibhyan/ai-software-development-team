interface SourceCodeViewProps {
  data: Record<string, unknown>;
}

export function SourceCodeView({ data }: SourceCodeViewProps) {
  const tree = data as {
    root?: string;
    files?: Array<{
      path: string;
      content: string;
      language?: string;
    }>;
    dependency_files?: string[];
  };

  if (!tree.files || tree.files.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No source code files generated.</p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Source Code</h2>
        <p className="text-sm text-muted-foreground">
          {tree.files.length} file{tree.files.length !== 1 ? 's' : ''}
          {tree.root ? ` in ${tree.root}` : ''}
        </p>
      </div>

      {tree.dependency_files && tree.dependency_files.length > 0 && (
        <div className="text-xs text-muted-foreground">
          Dependency files: {tree.dependency_files.join(', ')}
        </div>
      )}

      <div className="space-y-6">
        {tree.files.map((file, i) => (
          <div key={i} className="border rounded-lg overflow-hidden">
            <div className="bg-muted px-4 py-2 text-sm font-mono flex items-center justify-between">
              <span>{file.path}</span>
              {file.language && (
                <span className="text-xs text-muted-foreground">
                  {file.language}
                </span>
              )}
            </div>
            <pre className="text-xs p-4 overflow-x-auto bg-background">
              <code>{file.content}</code>
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
