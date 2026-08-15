import { Report } from '@/lib/api';

export default function ReportView({ report }: { report: Report }) {
  return (
    <div className="border border-(--completed) bg-(--panel) p-6 mt-6 space-y-4">
      <div>
        <div className="text-xs mono text-(--completed) mb-1">RÉSUMÉ</div>
        <p className="text-sm">{report.summary}</p>
      </div>

      {report.key_findings.length > 0 && (
        <div>
          <div className="text-xs mono text-(--text-dim) mb-1">FAITS CLÉS</div>
          <ul className="text-sm space-y-1 list-disc list-inside">
            {report.key_findings.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        </div>
      )}

      {report.recommendations.length > 0 && (
        <div>
          <div className="text-xs mono text-(--text-dim) mb-1">RECOMMANDATIONS</div>
          <ul className="text-sm space-y-1 list-disc list-inside">
            {report.recommendations.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}

      {report.risks.length > 0 && (
        <div>
          <div className="text-xs mono text-(--needs-review) mb-1">LIMITES / RISQUES</div>
          <ul className="text-sm space-y-1 list-disc list-inside">
            {report.risks.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}

      {report.sources.length > 0 && (
        <div>
          <div className="text-xs mono text-(--text-dim) mb-1">SOURCES</div>
          <ul className="text-xs space-y-1">
            {report.sources.map((s, i) => (
              <li key={i}><a href={s} target="_blank" rel="noreferrer" className="text-(--running) underline">{s}</a></li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}