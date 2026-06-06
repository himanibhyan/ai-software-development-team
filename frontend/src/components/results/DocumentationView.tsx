interface DocumentationViewProps {
  data: Record<string, unknown>;
}

export function DocumentationView({ data }: DocumentationViewProps) {
  const docs = data as {
    readme?: string;
    api_docs?: string;
    setup_guide?: string;
    architecture_overview?: string;
    contributing_guide?: string;
  };

  if (!docs.readme) {
    return (
      <p className="text-sm text-muted-foreground">No documentation generated.</p>
    );
  }

  const sections: Array<{ key: string; label: string }> = [
    { key: 'readme', label: 'README' },
    { key: 'setup_guide', label: 'Setup Guide' },
    { key: 'api_docs', label: 'API Documentation' },
    { key: 'architecture_overview', label: 'Architecture Overview' },
    { key: 'contributing_guide', label: 'Contributing Guide' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Documentation</h2>
      {sections.map(
        ({ key, label }) =>
          docs[key as keyof typeof docs] && (
            <section key={key}>
              <h3 className="text-lg font-semibold mb-2">{label}</h3>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <pre className="text-sm whitespace-pre-wrap bg-muted p-4 rounded-lg font-sans leading-relaxed">
                  {docs[key as keyof typeof docs]}
                </pre>
              </div>
            </section>
          )
      )}
    </div>
  );
}
