import { Download, FileText, Image as ImageIcon, Table2 } from 'lucide-react';
import { apiUrl } from '../api';
import { AnalysisPayload, HealthStatus } from '../types';

interface AcademicAnalysisTabProps {
  analysis: AnalysisPayload | null;
  health: HealthStatus | null;
}

function metric(value?: number, digits = 4) {
  return typeof value === 'number' ? value.toFixed(digits) : 'N/A';
}

function renderInlineMarkdown(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-black text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

function MarkdownReport({ report }: { report: string }) {
  if (!report.trim()) {
    return <p>The current backend has not generated an analysis report yet.</p>;
  }

  const blocks: string[][] = [];
  let current: string[] = [];
  report.split('\n').forEach((line) => {
    if (!line.trim()) {
      if (current.length) blocks.push(current);
      current = [];
    } else {
      current.push(line);
    }
  });
  if (current.length) blocks.push(current);

  return (
    <div className="space-y-6 text-sm leading-7 text-[#d4ddd1]">
      {blocks.map((block, blockIndex) => {
        const first = block[0].trim();
        if (first.startsWith('## ')) {
          const rest = block.slice(1).join(' ').trim();
          return (
            <div key={blockIndex} className="space-y-3">
              <h3 className="text-lg font-black text-white tracking-tight">
                {first.replace(/^##\s+/, '')}
              </h3>
              {rest && <p className="max-w-4xl">{renderInlineMarkdown(rest)}</p>}
            </div>
          );
        }
        if (first.startsWith('### ')) {
          const rest = block.slice(1).join(' ').trim();
          return (
            <div key={blockIndex} className="space-y-3">
              <h4 className="text-xs font-black text-[#53e076] uppercase tracking-wider font-mono">
                {first.replace(/^###\s+/, '')}
              </h4>
              {rest && <p className="max-w-4xl">{renderInlineMarkdown(rest)}</p>}
            </div>
          );
        }
        if (block.every((line) => line.trim().startsWith('|'))) {
          const rows = block
            .filter((line) => !/^\|\s*-+/.test(line.trim()))
            .map((line) =>
              line
                .trim()
                .replace(/^\|/, '')
                .replace(/\|$/, '')
                .split('|')
                .map((cell) => cell.trim())
            );
          const [headers, ...bodyRows] = rows;
          return (
            <div key={blockIndex} className="overflow-x-auto rounded-xl border border-white/10 bg-black/20">
              <table className="w-full text-left text-xs">
                <thead className="bg-white/5 text-[#bccbb9] font-mono uppercase text-[9px] tracking-wider">
                  <tr>
                    {headers.map((header) => (
                      <th key={header} className="px-4 py-3">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {bodyRows.map((row, rowIndex) => (
                    <tr key={`${blockIndex}-${rowIndex}`}>
                      {row.map((cell, cellIndex) => (
                        <td key={`${blockIndex}-${rowIndex}-${cellIndex}`} className="px-4 py-3 text-[#d4ddd1]">
                          {renderInlineMarkdown(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return (
          <p key={blockIndex} className="max-w-4xl">
            {renderInlineMarkdown(block.join(' '))}
          </p>
        );
      })}
    </div>
  );
}

export default function AcademicAnalysisTab({ analysis, health }: AcademicAnalysisTabProps) {
  const evaluation = analysis?.evaluation || {};
  const selectedAlgorithm = evaluation.algorithm || health?.selected_algorithm || 'unknown';
  const modelRows = [
    { model: 'KMeans', values: evaluation.kmeans },
    { model: 'GMM', values: evaluation.gmm },
    { model: 'DBSCAN', values: evaluation.dbscan },
  ];
  const kRows = Object.entries(analysis?.k_eval || {});
  const diagnosticPlots = Object.entries(analysis?.diagnostic_plots || {});
  const cohesionRows = analysis?.cohesion_separation || [];

  const handleDownload = () => {
    const reportText =
      analysis?.analysis_report ||
      [
        'Spotify Vibe Check | Academic Analysis Report',
        '============================================',
        `Selected Algorithm: ${selectedAlgorithm}`,
        `Silhouette Coefficient: ${metric(evaluation.silhouette)}`,
        `Davies-Bouldin Index: ${metric(evaluation.davies_bouldin)}`,
        `Clusters: ${evaluation.n_clusters ?? 'N/A'}`,
      ].join('\n');
    const element = document.createElement('a');
    const file = new Blob([reportText], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = 'vibe_check_analytical_report.txt';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="space-y-8" id="academic-analysis-tab">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-2xl font-black text-white tracking-tight">Academic Analysis</h3>
          <p className="text-sm text-[#bccbb9] mt-0.5">Live metrics from the trained clustering artifacts</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-white/10 text-white font-semibold text-xs hover:bg-white/5 active:scale-95 transition-all"
          >
            <Download size={14} />
            Download Summary
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none">
        <div className="glass-card p-5 rounded-xl border-l-4 border-l-[#53e076]">
          <p className="text-[#bccbb9] text-[9px] font-mono uppercase tracking-wider mb-1 font-bold">Selected Algorithm</p>
          <h3 className="text-lg font-black text-[#53e076] mt-1.5">{selectedAlgorithm}</h3>
        </div>
        <div className="glass-card p-5 rounded-xl">
          <p className="text-[#bccbb9] text-[9px] font-mono uppercase tracking-wider mb-1 font-bold">Silhouette Score</p>
          <h3 className="text-xl font-black text-white mt-1.5 font-mono">{metric(evaluation.silhouette)}</h3>
        </div>
        <div className="glass-card p-5 rounded-xl">
          <p className="text-[#bccbb9] text-[9px] font-mono uppercase tracking-wider mb-1 font-bold">Davies-Bouldin Index</p>
          <h3 className="text-xl font-black text-white mt-1.5 font-mono">{metric(evaluation.davies_bouldin)}</h3>
        </div>
        <div className="glass-card p-5 rounded-xl">
          <p className="text-[#bccbb9] text-[9px] font-mono uppercase tracking-wider mb-1 font-bold">Total Clusters</p>
          <h3 className="text-xl font-black text-white mt-1.5 font-mono">{evaluation.n_clusters ?? health?.cluster_count ?? 'N/A'}</h3>
        </div>
      </div>

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {diagnosticPlots.map(([key, plot]) => (
          <div key={key} className="glass-card rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ImageIcon size={15} className="text-[#53e076]" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-white font-mono">{plot.title}</h4>
              </div>
              <span className={`text-[9px] font-mono ${plot.available ? 'text-[#53e076]' : 'text-[#ffb4ab]'}`}>
                {plot.available ? 'available' : 'missing'}
              </span>
            </div>
            {plot.available ? (
              <div className="bg-white p-2">
                <img src={apiUrl(plot.url)} alt={plot.title} className="w-full h-64 object-contain" />
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-xs text-[#bccbb9] p-6 text-center">
                Re-run train_pipeline.py to regenerate this diagnostic plot.
              </div>
            )}
          </div>
        ))}
      </section>

      <section className="glass-pane glass-panel rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10 flex justify-between items-center">
          <h4 className="text-xs font-bold uppercase tracking-wider text-white font-mono">Comparative Performance Matrix</h4>
          <span className="text-[#bccbb9] text-[10px] font-mono">Generated from current model artifacts</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="bg-white/5 border-b border-white/10 text-[#bccbb9] font-mono text-[9px]">
                <th className="px-6 py-3.5 uppercase">Model</th>
                <th className="px-6 py-3.5 uppercase">Silhouette</th>
                <th className="px-6 py-3.5 uppercase">Davies-Bouldin</th>
                <th className="px-6 py-3.5 uppercase">Clusters</th>
                <th className="px-6 py-3.5 uppercase">Noise %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {modelRows.map((row) => {
                const selected = row.model.toLowerCase() === selectedAlgorithm.toLowerCase();
                return (
                  <tr key={row.model} className={selected ? 'bg-[#53e076]/5 font-semibold text-white' : 'text-[#bccbb9]'}>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${selected ? 'bg-[#53e076]' : 'bg-white/20'}`}></span>
                        {row.model}
                      </div>
                    </td>
                    <td className={`px-6 py-4 font-mono ${selected ? 'text-[#53e076] font-bold' : ''}`}>{metric(row.values?.silhouette)}</td>
                    <td className="px-6 py-4 font-mono">{metric(row.values?.davies_bouldin)}</td>
                    <td className="px-6 py-4 font-mono">{row.values?.n_clusters ?? 'N/A'}</td>
                    <td className="px-6 py-4 font-mono">{metric(row.values?.noise_pct, 1)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 select-none">
        <div className="glass-card p-6 rounded-xl flex flex-col h-[350px]">
          <h5 className="text-xs font-bold uppercase text-white font-mono tracking-wide mb-4">PCA Cumulative Explained Variance</h5>
          <div className="relative h-56 rounded-xl border border-white/5 bg-black/20 px-4 pt-5 pb-8">
            {[25, 50, 75, 95].map((tick) => (
              <div
                key={tick}
                className="absolute left-4 right-4 border-t border-white/5"
                style={{ bottom: `${8 + tick * 0.84}%` }}
              >
                <span className="absolute -top-2 right-0 text-[8px] text-[#bccbb9]/60 font-mono">{tick}%</span>
              </div>
            ))}
            <div className="relative z-10 h-full flex items-end gap-3">
            {(analysis?.pca_report.cumulative || []).map((value, index) => (
              <div key={index} className="flex-1 h-full flex flex-col justify-end gap-2 min-w-0">
                <div
                  className="relative rounded-t-lg bg-gradient-to-t from-[#53e076] to-[#37d7ff] shadow-[0_0_18px_rgba(83,224,118,0.22)] border border-white/10"
                  style={{ height: `${Math.max(8, Math.round(value * 100))}%` }}
                  title={`${(value * 100).toFixed(1)}% cumulative variance`}
                >
                  <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-[8px] font-mono text-[#53e076]">
                    {(value * 100).toFixed(0)}%
                  </span>
                </div>
                <span className="text-[8px] text-[#bccbb9] font-mono text-center">PC{index + 1}</span>
              </div>
            ))}
            </div>
          </div>
          <p className="text-[10px] text-center text-[#bccbb9] mt-3 font-mono">
            Components selected: <span className="text-[#53e076] font-bold">{analysis?.pca_report.n_components ?? 'N/A'}</span>
          </p>
        </div>

        <div className="glass-card p-6 rounded-xl flex flex-col h-[350px]">
          <h5 className="text-xs font-bold uppercase text-white font-mono tracking-wide mb-4">K Search Evaluation</h5>
          <div className="flex-grow overflow-y-auto custom-scrollbar pr-2">
            <table className="w-full text-left text-xs">
              <thead className="text-[#bccbb9] font-mono text-[9px] uppercase">
                <tr>
                  <th className="py-2">k</th>
                  <th className="py-2">Inertia</th>
                  <th className="py-2">Silhouette</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {kRows.map(([k, row]) => (
                  <tr key={k}>
                    <td className="py-2 font-mono text-white">{k}</td>
                    <td className="py-2 font-mono text-[#bccbb9]">{Math.round(row.inertia).toLocaleString()}</td>
                    <td className="py-2 font-mono text-[#53e076]">{metric(row.silhouette)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <section className="glass-pane glass-panel rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Table2 size={15} className="text-[#53e076]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-white font-mono">Cohesion and Separation</h4>
          </div>
          <span className="text-[#bccbb9] text-[10px] font-mono">PCA-space distances by cluster</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="bg-white/5 border-b border-white/10 text-[#bccbb9] font-mono text-[9px]">
                <th className="px-6 py-3.5 uppercase">Cluster</th>
                <th className="px-6 py-3.5 uppercase">Cohesion</th>
                <th className="px-6 py-3.5 uppercase">Separation</th>
                <th className="px-6 py-3.5 uppercase">Sep / Coh</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {cohesionRows.map((row) => (
                <tr key={row.cluster_id} className="text-[#bccbb9]">
                  <td className="px-6 py-4 text-white font-semibold">{row.cluster_name}</td>
                  <td className="px-6 py-4 font-mono">{metric(row['cohesion (avg intra-dist)'])}</td>
                  <td className="px-6 py-4 font-mono">{metric(row['separation (min inter-dist)'])}</td>
                  <td className="px-6 py-4 font-mono text-[#53e076]">{metric(row['ratio (sep/coh)'])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="glass-panel p-6 sm:p-8 rounded-xl space-y-4">
        <div className="flex items-center gap-3">
          <FileText size={24} className="text-[#53e076]" />
          <h4 className="text-base font-black text-white uppercase tracking-wider font-mono">Analytical Interpretation</h4>
        </div>
        <div className="border-l-2 border-[#53e076]/30 pl-6 py-2 select-text">
          <MarkdownReport
            report={
              analysis?.analysis_report ||
              `The current backend selected ${selectedAlgorithm} using silhouette score as the production clustering path.`
            }
          />
        </div>
      </section>
    </div>
  );
}
