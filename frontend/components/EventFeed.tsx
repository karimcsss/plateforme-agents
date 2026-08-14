import { LogEvent } from '@/lib/useRunStream';

const EVENT_LABELS: Record<string, string> = {
  llm_call: 'Génération',
  tool_call: 'Recherche web',
  error: 'Erreur',
  status_change: 'Changement de statut',
};

export default function EventFeed({ logs }: { logs: LogEvent[] }) {
  return (
    <div className="border border-[var(--border)] h-[500px] overflow-y-auto p-3 space-y-2">
      {logs.length === 0 && (
        <div className="text-[var(--text-dim)] text-sm">En attente du premier événement…</div>
      )}
      {logs.map((log) => (
        <div key={log.id} className="text-xs border-b border-[var(--border)] pb-2">
          <div className="flex justify-between">
            <span className="mono text-[var(--text-dim)]">{log.agent_id || 'système'}</span>
            <span className="text-[var(--text-dim)]">{EVENT_LABELS[log.event_type]}</span>
          </div>
          {log.latency_ms !== null && (
            <div className="mono text-[var(--text-dim)] mt-1">{log.latency_ms}ms</div>
          )}
        </div>
      ))}
    </div>
  );
}