import { useEffect, useRef, useState } from 'react';
import { getStreamUrl } from './api';

export interface LogEvent {
  id: string;
  agent_id: string | null;
  event_type: 'llm_call' | 'tool_call' | 'error' | 'status_change';
  payload: Record<string, unknown>;
  latency_ms: number | null;
  created_at: string;
}

export function useRunStream(runId: string) {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [status, setStatus] = useState<string>('planning');
  const [streamEnded, setStreamEnded] = useState(false);
  const seenIds = useRef(new Set<string>());

  useEffect(() => {
    const source = new EventSource(getStreamUrl(runId));

    source.addEventListener('log', (e) => {
      const log: LogEvent = JSON.parse(e.data);
      if (!seenIds.current.has(log.id)) {
        seenIds.current.add(log.id);
        setLogs((prev) => [...prev, log]);
      }
    });

    source.addEventListener('run_status', (e) => {
      const data = JSON.parse(e.data);
      setStatus(data.status);
    });

    source.addEventListener('stream_end', () => {
      setStreamEnded(true);
      source.close();
    });

    source.onerror = () => {
      source.close();
      setStreamEnded(true);
    };

    return () => source.close();
  }, [runId]);

  return { logs, status, streamEnded };
}