interface ReviewViewProps {
  data: Record<string, unknown>;
}

export function ReviewView({ data }: ReviewViewProps) {
  const review = data as {
    summary?: string;
    overall_score?: number;
    comments?: Array<{
      file_path: string;
      line_start?: number;
      line_end?: number;
      severity?: string;
      message: string;
      suggestion?: string;
    }>;
    strengths?: string[];
    weaknesses?: string[];
    security_concerns?: string[];
  };

  if (!review.summary) {
    return (
      <p className="text-sm text-muted-foreground">No code review available.</p>
    );
  }

  const scoreColor =
    review.overall_score != null
      ? review.overall_score >= 7
        ? 'text-emerald-500'
        : review.overall_score >= 4
          ? 'text-amber-500'
          : 'text-destructive'
      : '';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Code Review</h2>
        {review.overall_score != null && (
          <div className="text-center">
            <div className={`text-3xl font-bold ${scoreColor}`}>
              {review.overall_score.toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">/ 10</p>
          </div>
        )}
      </div>

      {review.summary && (
        <section>
          <h3 className="font-semibold mb-1">Summary</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {review.summary}
          </p>
        </section>
      )}

      {review.strengths && review.strengths.length > 0 && (
        <section>
          <h3 className="font-semibold mb-1 text-emerald-600 dark:text-emerald-400">Strengths</h3>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            {review.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </section>
      )}

      {review.weaknesses && review.weaknesses.length > 0 && (
        <section>
          <h3 className="font-semibold mb-1 text-amber-600 dark:text-amber-400">Weaknesses</h3>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            {review.weaknesses.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </section>
      )}

      {review.security_concerns && review.security_concerns.length > 0 && (
        <section>
          <h3 className="font-semibold mb-1 text-destructive">Security Concerns</h3>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            {review.security_concerns.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </section>
      )}

      {review.comments && review.comments.length > 0 && (
        <section>
          <h3 className="font-semibold mb-2">
            Comments ({review.comments.length})
          </h3>
          <div className="space-y-3">
            {review.comments.map((c, i) => {
              const sevColor =
                c.severity === 'critical' || c.severity === 'error'
                  ? 'border-destructive/50'
                  : c.severity === 'warning'
                    ? 'border-amber-500/50'
                    : 'border-border';
              return (
                <div key={i} className={`border-l-4 ${sevColor} pl-3 py-2`}>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <span className="font-mono">{c.file_path}</span>
                    {c.line_start != null && (
                      <span>
                        L{c.line_start}
                        {c.line_end != null && c.line_end !== c.line_start
                          ? `-${c.line_end}`
                          : ''}
                      </span>
                    )}
                    {c.severity && (
                      <span className="capitalize">({c.severity})</span>
                    )}
                  </div>
                  <p className="text-sm">{c.message}</p>
                  {c.suggestion && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Suggestion: {c.suggestion}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
