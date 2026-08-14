const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RequiredAgent {
  id: string;
  role: string;
  goal: string;
  depends_on: string[];
}

export interface Plan {
  objective: string;
  required_agents: RequiredAgent[];
  workflow: string;
  requires_human_approval: boolean;
}

export interface Run {
  id: string;
  problem_statement: string;
  status: string;
  plan: Plan | null;
  error_detail: Record<string, unknown> | null;
}

export async function createRun(problemStatement: string): Promise<Run> {
  const res = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problem_statement: problemStatement }),
  });
  if (!res.ok) throw new Error('Échec de la création du run');
  return res.json();
}

export async function getRun(runId: string): Promise<Run> {
  const res = await fetch(`${API_BASE}/runs/${runId}`);
  if (!res.ok) throw new Error('Run introuvable');
  return res.json();
}

export function getStreamUrl(runId: string): string {
  return `${API_BASE}/runs/${runId}/stream`;
}
export async function approveRun(runId: string, decision: 'approved' | 'rejected'): Promise<Run> {
  const res = await fetch(`${API_BASE}/runs/${runId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(`Échec de la décision (${res.status}) : ${JSON.stringify(body)}`);
  }
  return res.json();
}