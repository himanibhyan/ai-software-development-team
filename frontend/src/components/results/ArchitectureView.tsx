interface ArchitectureViewProps {
  data: Record<string, unknown>;
}

export function ArchitectureView({ data }: ArchitectureViewProps) {
  const arch = data as {
    title?: string;
    overview?: string;
    architecture_pattern?: string;
    components?: Array<{
      name: string;
      description: string;
      technology?: string;
      responsibilities?: string[];
      dependencies?: string[];
    }>;
    data_flow?: Array<Record<string, string>>;
    tech_stack?: Record<string, string>;
    deployment_strategy?: string;
    security_considerations?: string[];
    scalability_notes?: string;
    monitoring_strategy?: string;
    folder_structure?: {
      root?: string;
      entries?: Array<{ name: string; type?: string; children?: Array<{ name: string; type?: string }>; description?: string }>;
    };
    database_design?: {
      engine?: string;
      tables?: Array<{ name: string; columns: Array<{ name: string; type?: string; constraints?: string }>; description: string; relationships?: string[] }>;
      orm?: string;
      caching_strategy?: string;
    };
    api_spec?: {
      protocol?: string;
      base_url?: string;
      endpoints?: Array<{ path: string; method: string; description: string }>;
      auth_method?: string;
    };
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{arch.title ?? 'Architecture'}</h2>
        {arch.architecture_pattern && (
          <p className="text-sm text-muted-foreground mt-1">
            Pattern: {arch.architecture_pattern}
          </p>
        )}
      </div>

      {arch.overview && (
        <section>
          <h3 className="font-semibold mb-1">Overview</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {arch.overview}
          </p>
        </section>
      )}

      {arch.components && arch.components.length > 0 && (
        <section>
          <h3 className="font-semibold mb-2">
            Components ({arch.components.length})
          </h3>
          <div className="grid gap-3">
            {arch.components.map((c, i) => (
              <div key={i} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{c.name}</h4>
                  {c.technology && (
                    <span className="text-xs bg-muted px-2 py-0.5 rounded">
                      {c.technology}
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mb-2">
                  {c.description}
                </p>
                {c.responsibilities && c.responsibilities.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">
                      Responsibilities:
                    </p>
                    <ul className="list-disc list-inside text-xs text-muted-foreground space-y-0.5">
                      {c.responsibilities.map((r, j) => (
                        <li key={j}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {c.dependencies && c.dependencies.length > 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Dependencies: {c.dependencies.join(', ')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {arch.tech_stack && Object.keys(arch.tech_stack).length > 0 && (
        <section>
          <h3 className="font-semibold mb-2">Tech Stack</h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted">
                  <th className="text-left p-2 font-medium">Category</th>
                  <th className="text-left p-2 font-medium">Choice</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(arch.tech_stack).map(([k, v]) => (
                  <tr key={k} className="border-t">
                    <td className="p-2 capitalize">{k}</td>
                    <td className="p-2 font-mono text-xs">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {arch.deployment_strategy && (
        <section>
          <h3 className="font-semibold mb-1">Deployment Strategy</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {arch.deployment_strategy}
          </p>
        </section>
      )}

      {arch.security_considerations && arch.security_considerations.length > 0 && (
        <section>
          <h3 className="font-semibold mb-1">Security Considerations</h3>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            {arch.security_considerations.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </section>
      )}

      {arch.folder_structure?.entries && (
        <section>
          <h3 className="font-semibold mb-1">Folder Structure</h3>
          <pre className="text-xs bg-muted p-4 rounded-lg overflow-x-auto">
            {renderFolderTree(arch.folder_structure.root ?? 'root', arch.folder_structure.entries, '')}
          </pre>
        </section>
      )}
    </div>
  );
}

function renderFolderTree(
  _root: string,
  entries: Array<{ name: string; type?: string; children?: Array<{ name: string; type?: string }>; description?: string }>,
  indent: string
): string {
  let result = '';
  for (const e of entries) {
    const icon = e.type === 'directory' ? '📁' : '📄';
    result += `${indent}${icon} ${e.name}${e.description ? `  # ${e.description}` : ''}\n`;
    if (e.type === 'directory' && e.children) {
      result += renderFolderTree('', e.children, indent + '  ');
    }
  }
  return result;
}
