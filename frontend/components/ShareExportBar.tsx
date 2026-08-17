'use client';

import { useState } from 'react';
import { shareRun, getExportUrl } from '@/lib/api';

export default function ShareExportBar({ runId }: { runId: string }) {
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [copying, setCopying] = useState(false);

  async function handleShare() {
    const { share_url } = await shareRun(runId);
    const fullUrl = `${window.location.origin}${share_url}`;
    setShareUrl(fullUrl);
  }

  async function handleCopy() {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    setCopying(true);
    setTimeout(() => setCopying(false), 1500);
  }

  return (
    <div className="flex items-center gap-3 mt-4 text-sm">
      <a href={getExportUrl(runId, 'md')} className="text-(--running) underline">
        Exporter en Markdown
      </a>
      <a href={getExportUrl(runId, 'json')} className="text-(--running) underline">
        Exporter en JSON
      </a>
      {!shareUrl ? (
        <button onClick={handleShare} className="text-(--completed) underline">
          Générer un lien de partage
        </button>
      ) : (
        <button onClick={handleCopy} className="text-(--text-dim) mono text-xs">
          {copying ? 'Copié !' : shareUrl}
        </button>
      )}
    </div>
  );
}