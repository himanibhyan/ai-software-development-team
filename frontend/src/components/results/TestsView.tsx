interface TestsViewProps {
  data: Record<string, unknown>;
}

export function TestsView({ data }: TestsViewProps) {
  const suite = data as {
    test_framework?: string;
    test_config?: Record<string, unknown>;
    test_cases?: Array<{
      name: string;
      description: string;
      file_path: string;
      code: string;
      type?: string;
    }>;
    coverage_target?: number;
  };

  if (!suite.test_cases || suite.test_cases.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No test cases generated.</p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-2xl font-bold">Test Suite</h2>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {suite.test_framework && (
            <span>Framework: {suite.test_framework}</span>
          )}
          {suite.coverage_target != null && (
            <span>Coverage target: {(suite.coverage_target * 100).toFixed(0)}%</span>
          )}
        </div>
      </div>

      {suite.test_config && Object.keys(suite.test_config).length > 0 && (
        <div className="border rounded-lg p-4">
          <h3 className="text-sm font-medium mb-2">Test Configuration</h3>
          <pre className="text-xs text-muted-foreground">
            {JSON.stringify(suite.test_config, null, 2)}
          </pre>
        </div>
      )}

      <div className="space-y-4">
        {suite.test_cases.map((tc, i) => (
          <div key={i} className="border rounded-lg overflow-hidden">
            <div className="bg-muted px-4 py-2 flex items-center justify-between">
              <div>
                <span className="text-sm font-medium">{tc.name}</span>
                {tc.type && (
                  <span className="text-xs text-muted-foreground ml-2">
                    ({tc.type})
                  </span>
                )}
              </div>
              <span className="text-xs font-mono text-muted-foreground">
                {tc.file_path}
              </span>
            </div>
            {tc.description && (
              <div className="px-4 py-2 text-xs text-muted-foreground border-t">
                {tc.description}
              </div>
            )}
            <pre className="text-xs p-4 overflow-x-auto bg-background border-t">
              <code>{tc.code}</code>
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
