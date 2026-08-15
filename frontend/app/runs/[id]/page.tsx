'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import { getRun, approveRun, Run } from '@/lib/api';
import { useRunStream } from '@/lib/useRunStream';
import AgentGraph from '@/components/AgentGraph';
import EventFeed from '@/components/EventFeed';
import ReportView from '@/components/ReportView';

export default function RunPage() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<Run | null>(null);
  const [deciding, setDeciding] = useState(false);
  const decidingRef = useRef(false);
  const { logs, status } = useRunStream(id);

  useEffect(() => {
    getRun(id).then(setRun);
  }, [id]);

  async function handleDecision(decision: 'approved' | 'rejected') {
    if (decidingRef.current) return;
    decidingRef.current = true;
    setDeciding(true);
    try {
      const updated = await approveRun(id, decision);
      setRun(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setDeciding(false);
      decidingRef.current = false;
    }
  }

  if (!run) return <div className="p-8 text-(--text-dim)">Chargement…</div>;

  if (!run.plan) {
    return (
      <div className="p-8">
        <h1 className="text-xl mb-2">{run.problem_statement}</h1>
        <p className="text-(--failed)">Statut : {run.status}</p>
        {run.error_detail && (
          <pre className="mono text-xs mt-4 text-(--text-dim)">
            {JSON.stringify(run.error_detail, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  return (
    <main className="max-w-6xl mx-auto p-8">
      <h1 className="text-xl mb-1">{run.problem_statement}</h1>
      <p className="mono text-sm text-(--running) mb-4">Statut : {status}</p>

      {run.status === 'pending_approval' && (
        <div className="border border-(--needs-review) bg-(--panel) p-4 mb-6 flex items-center justify-between">
          <span className="text-sm">
            Ce plan nécessite une validation humaine avant exécution.
          </span>
          <div className="space-x-2">
            <button
              onClick={() => handleDecision('approved')}
              disabled={deciding}
              className="bg-(--completed) text-black px-4 py-1.5 text-sm font-medium disabled:opacity-50"
            >
              Approuver
            </button>
            <button
              onClick={() => handleDecision('rejected')}
              disabled={deciding}
              className="bg-(--failed) text-black px-4 py-1.5 text-sm font-medium disabled:opacity-50"
            >
              Rejeter
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <AgentGraph agents={run.plan.required_agents} logs={logs} />
        </div>
        <div>
          <EventFeed logs={logs} />
        </div>
      </div>
      {run.report && <ReportView report={run.report} />}
    </main>
  );
}