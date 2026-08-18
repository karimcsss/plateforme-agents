'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createRun } from '@/lib/api';


export default function Home() {
  const [problem, setProblem] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!problem.trim()) return;
    setLoading(true);
    try {
      const run = await createRun(problem);
      router.push(`/runs/${run.id}`);
    } catch {
      setLoading(false);
      alert('Échec de la soumission — vérifie que le backend tourne sur le port 8000.');
    }
  }

  return (
    <main className="max-w-2xl mx-auto mt-24 px-4">
      <h1 className="text-2xl font-medium mb-2">Plateforme Multi-Agents</h1>
      <p className="text-(--text-dim) mb-8">
        Soumets un problème. Une équipe d&apos;agents IA sera générée dynamiquement pour y répondre.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={problem}
          onChange={(e) => setProblem(e.target.value)}
          placeholder="Ex : Faut-il investir dans l'immobilier ou la bourse en 2026 ?"
          className="w-full bg-(--panel) border border-(--border) p-4 h-32 text-(--text) focus:outline-none focus:border-(--running)"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-(--running) text-black px-6 py-2 font-medium disabled:opacity-50"
        >
          {loading ? 'Envoi…' : 'Lancer'}
        </button>
      </form>
    </main>
  );
}