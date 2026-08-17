'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getPublicRun, Run } from '@/lib/api';
import ReportView from '@/components/ReportView';

export default function PublicSharePage() {
  const { token } = useParams<{ token: string }>();
  const [run, setRun] = useState<Run | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPublicRun(token).then(setRun).catch((e) => setError(e.message));
  }, [token]);

  if (error) return <div className="p-8 text-(--failed)">{error}</div>;
  if (!run) return <div className="p-8 text-(--text-dim)">Chargement…</div>;

  return (
    <main className="max-w-3xl mx-auto p-8">
      <div className="text-xs mono text-(--text-dim) mb-2">RAPPORT PARTAGÉ — LECTURE SEULE</div>
      <h1 className="text-xl mb-6">{run.problem_statement}</h1>
      {run.report ? (
        <ReportView report={run.report} />
      ) : (
        <p className="text-(--text-dim)">Aucun rapport disponible pour ce run.</p>
      )}
    </main>
  );
}