'use client';

import { useMemo } from 'react';
import ReactFlow, { Background, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';
import AgentNode from './AgentNode';
import { RequiredAgent } from '@/lib/api';
import { LogEvent } from '@/lib/useRunStream';

const nodeTypes = { agent: AgentNode };

function computeAgentStatus(agentId: string, logs: LogEvent[]): string {
  const agentLogs = logs.filter((l) => l.agent_id === agentId);
  if (agentLogs.length === 0) return 'pending';
  const last = agentLogs[agentLogs.length - 1];
  if (last.event_type === 'error') return 'failed';
  if (last.event_type === 'llm_call') return 'completed';
  return 'running';
}

export default function AgentGraph({ agents, logs }: { agents: RequiredAgent[]; logs: LogEvent[] }) {
  const { nodes, edges } = useMemo(() => {
    // Layout simple par vagues (meme logique que le backend _topological_batches)
    const done = new Set<string>();
    const levels: RequiredAgent[][] = [];
    const remaining = [...agents];

    while (remaining.length > 0) {
      const batch = remaining.filter((a) => a.depends_on.every((d) => done.has(d)));
      if (batch.length === 0) break;
      levels.push(batch);
      batch.forEach((a) => done.add(a.id));
      remaining.splice(0, remaining.length, ...remaining.filter((a) => !batch.includes(a)));
    }

    const nodes: Node[] = [];
    levels.forEach((level, levelIdx) => {
      level.forEach((agent, i) => {
        nodes.push({
          id: agent.id,
          type: 'agent',
          position: { x: i * 220 - (level.length - 1) * 110, y: levelIdx * 140 },
          data: { role: agent.role, agentId: agent.id, status: computeAgentStatus(agent.id, logs) },
        });
      });
    });

    const edges: Edge[] = agents.flatMap((a) =>
      a.depends_on.map((dep) => ({
        id: `${dep}-${a.id}`,
        source: dep,
        target: a.id,
        animated: computeAgentStatus(a.id, logs) === 'running',
        style: { stroke: 'var(--border)' },
      }))
    );

    return { nodes, edges };
  }, [agents, logs]);

  return (
    <div className="h-[500px] border border-[var(--border)]">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView proOptions={{ hideAttribution: true }}>
        <Background color="var(--border)" gap={20} />
      </ReactFlow>
    </div>
  );
}