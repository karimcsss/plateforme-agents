import { Handle, Position } from 'reactflow';

const STATUS_COLORS: Record<string, string> = {
  pending: 'var(--pending)',
  running: 'var(--running)',
  completed: 'var(--completed)',
  failed: 'var(--failed)',
  needs_review: 'var(--needs-review)',
};

export default function AgentNode({ data }: { data: { role: string; agentId: string; status: string } }) {
  const color = STATUS_COLORS[data.status] || STATUS_COLORS.pending;

  return (
    <div
      style={{ borderColor: color }}
      className="px-4 py-3 rounded-none border-2 bg-[var(--panel)] min-w-[180px]"
    >
      <Handle type="target" position={Position.Top} style={{ background: color }} />
      <div className="text-xs mono" style={{ color }}>{data.status}</div>
      <div className="font-medium text-sm mt-1">{data.role}</div>
      <div className="text-xs mono text-[var(--text-dim)] mt-1">{data.agentId}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: color }} />
    </div>
  );
}