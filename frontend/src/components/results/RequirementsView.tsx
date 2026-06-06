interface RequirementsViewProps {
  data: Record<string, unknown>;
}

export function RequirementsView({ data }: RequirementsViewProps) {
  const reqs = data as {
    title?: string;
    purpose?: string;
    scope?: string;
    functional_requirements?: Array<{
      id: string;
      description: string;
      priority: string;
    }>;
    non_functional_requirements?: Array<{
      id: string;
      description: string;
      category: string;
    }>;
    user_stories?: Array<{
      id: string;
      description: string;
      priority: string;
    }>;
    constraints?: string[];
    assumptions?: string[];
    open_issues?: string[];
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{reqs.title ?? 'Requirements'}</h2>
      </div>

      {reqs.purpose && (
        <section>
          <h3 className="font-semibold mb-1">Purpose</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {reqs.purpose}
          </p>
        </section>
      )}

      {reqs.scope && (
        <section>
          <h3 className="font-semibold mb-1">Scope</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {reqs.scope}
          </p>
        </section>
      )}

      {reqs.functional_requirements && reqs.functional_requirements.length > 0 && (
        <section>
          <h3 className="font-semibold mb-2">
            Functional Requirements ({reqs.functional_requirements.length})
          </h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted">
                  <th className="text-left p-2 font-medium">ID</th>
                  <th className="text-left p-2 font-medium">Description</th>
                  <th className="text-left p-2 font-medium">Priority</th>
                </tr>
              </thead>
              <tbody>
                {reqs.functional_requirements.map((fr) => (
                  <tr key={fr.id} className="border-t">
                    <td className="p-2 font-mono text-xs">{fr.id}</td>
                    <td className="p-2">{fr.description}</td>
                    <td className="p-2">{fr.priority}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {reqs.non_functional_requirements && reqs.non_functional_requirements.length > 0 && (
        <section>
          <h3 className="font-semibold mb-2">
            Non-Functional Requirements ({reqs.non_functional_requirements.length})
          </h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted">
                  <th className="text-left p-2 font-medium">ID</th>
                  <th className="text-left p-2 font-medium">Description</th>
                  <th className="text-left p-2 font-medium">Category</th>
                </tr>
              </thead>
              <tbody>
                {reqs.non_functional_requirements.map((nfr) => (
                  <tr key={nfr.id} className="border-t">
                    <td className="p-2 font-mono text-xs">{nfr.id}</td>
                    <td className="p-2">{nfr.description}</td>
                    <td className="p-2 capitalize">{nfr.category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {reqs.user_stories && reqs.user_stories.length > 0 && (
        <section>
          <h3 className="font-semibold mb-2">
            User Stories ({reqs.user_stories.length})
          </h3>
          <div className="space-y-2">
            {reqs.user_stories.map((us) => (
              <div key={us.id} className="border rounded-lg p-3 text-sm">
                <span className="font-mono text-xs text-muted-foreground">
                  {us.id}
                </span>{' '}
                <span>{us.description}</span>
                <span className="ml-2 text-xs text-muted-foreground">
                  ({us.priority})
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {reqs.constraints && reqs.constraints.length > 0 && (
        <section>
          <h3 className="font-semibold mb-1">Constraints</h3>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            {reqs.constraints.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </section>
      )}

      {reqs.assumptions && reqs.assumptions.length > 0 && (
        <section>
          <h3 className="font-semibold mb-1">Assumptions</h3>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            {reqs.assumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </section>
      )}

      {reqs.open_issues && reqs.open_issues.length > 0 && (
        <section>
          <h3 className="font-semibold mb-1">Open Issues</h3>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            {reqs.open_issues.map((o, i) => (
              <li key={i}>{o}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
