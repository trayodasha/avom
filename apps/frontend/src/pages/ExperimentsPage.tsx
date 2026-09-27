import React, { useState, useEffect } from 'react';
import { GitCompare, Layers, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
import { getAuthHeaders, getActiveProject } from '../lib/auth';

interface EvaluationRun {
  id: string;
  name: string;
  status: string;
  configuration_snapshot: Record<string, any>;
  aggregate_metrics: Record<string, number>;
  total_examples: number;
  duration_ms: number;
  created_at: string;
}

interface ComparisonData {
  runs: EvaluationRun[];
  metric_keys: string[];
  matrix: Record<string, Record<string, number | null>>;
  deltas: Record<string, Record<string, number | null>>;
}

export const ExperimentsPage: React.FC = () => {
  const activeProj = getActiveProject();
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch all runs for the workspace
  useEffect(() => {
    const fetchRuns = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/evaluations?project_id=${activeProj.id}`, {
          headers: getAuthHeaders(),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: EvaluationRun[] = await res.json();
        const completed = data.filter((r) => r.status === 'COMPLETED');
        setRuns(completed);

        // Pre-select top 2 completed runs by default
        if (completed.length >= 2) {
          setSelectedRunIds([completed[0].id, completed[1].id]);
        } else if (completed.length === 1) {
          setSelectedRunIds([completed[0].id]);
        }
      } catch (err: any) {
        console.error(err);
        setErrorMsg('Failed to load completed evaluation runs.');
      } finally {
        setLoading(false);
      }
    };
    fetchRuns();
  }, [activeProj.id]);

  // Fetch comparison whenever selectedRunIds changes
  useEffect(() => {
    if (selectedRunIds.length === 0) {
      setComparison(null);
      return;
    }

    const fetchComparison = async () => {
      try {
        const queryParams = selectedRunIds.map((id) => `run_ids=${id}`).join('&');
        const res = await fetch(`/api/v1/experiments/compare?${queryParams}`, {
          headers: getAuthHeaders(),
        });
        if (res.ok) {
          const data: ComparisonData = await res.json();
          setComparison(data);
        }
      } catch (err) {
        console.error(err);
      }
    };

    fetchComparison();
  }, [selectedRunIds]);

  const toggleRunSelection = (runId: string) => {
    if (selectedRunIds.includes(runId)) {
      if (selectedRunIds.length > 1) {
        setSelectedRunIds(selectedRunIds.filter((id) => id !== runId));
      }
    } else {
      if (selectedRunIds.length < 4) {
        setSelectedRunIds([...selectedRunIds, runId]);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">RAG Configuration Experiments</h2>
          <p className="text-sm text-slate-400 mt-1">
            Compare retrieval pipelines, chunking parameters, and cross-encoders head-to-head on identical evaluation datasets.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl flex items-center gap-2 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Run Selectors */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-white">
            <Layers className="w-4 h-4 text-indigo-400" />
            Select Experiments to Compare (2 - 4 runs)
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            {selectedRunIds.length} of {runs.length} selected
          </span>
        </div>

        {loading ? (
          <p className="text-xs text-slate-400">Loading experiments...</p>
        ) : runs.length === 0 ? (
          <p className="text-xs text-slate-400">
            No completed evaluation runs found in this workspace. Run at least 2 evaluations in the{' '}
            <strong className="text-indigo-400">Evaluations</strong> tab to compare architectures.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2 pt-1">
            {runs.map((r) => {
              const isSelected = selectedRunIds.includes(r.id);
              return (
                <button
                  key={r.id}
                  onClick={() => toggleRunSelection(r.id)}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-mono transition-all flex items-center gap-2 cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-200'
                      : 'bg-slate-950/70 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-indigo-400' : 'bg-slate-600'}`} />
                  {r.name}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Comparison Matrix Table */}
      {comparison && comparison.runs.length > 0 && (
        <div className="rounded-xl bg-slate-900/80 border border-slate-800 overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
            <div className="flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-semibold text-white">
                Head-to-Head Architecture Matrix & Delta Analysis
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Baseline: {comparison.runs[0].name}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-mono text-[11px] border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Metric / Parameter</th>
                  {comparison.runs.map((run, idx) => (
                    <th key={run.id} className="p-3.5">
                      <span className="text-white block font-sans">{run.name}</span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {idx === 0 ? '(Baseline)' : `Experiment ${String.fromCharCode(65 + idx)}`}
                      </span>
                    </th>
                  ))}
                  {comparison.runs.length > 1 && <th className="p-3.5">Delta (Exp B vs Baseline)</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300 font-mono">
                {/* Configuration Parameters */}
                <tr className="bg-slate-950/30">
                  <td className="p-3.5 font-sans font-medium text-white">Retrieval Type</td>
                  {comparison.runs.map((run) => (
                    <td key={run.id} className="p-3.5 text-indigo-300 uppercase">
                      {run.configuration_snapshot?.retrieval_type || 'hybrid'}
                    </td>
                  ))}
                  {comparison.runs.length > 1 && <td className="p-3.5 text-slate-500">&mdash;</td>}
                </tr>
                <tr className="bg-slate-950/30">
                  <td className="p-3.5 font-sans font-medium text-white">Cross-Encoder Reranker</td>
                  {comparison.runs.map((run) => (
                    <td key={run.id} className="p-3.5">
                      {run.configuration_snapshot?.reranking ? (
                        <span className="text-emerald-400">Enabled</span>
                      ) : (
                        <span className="text-slate-500">Disabled</span>
                      )}
                    </td>
                  ))}
                  {comparison.runs.length > 1 && <td className="p-3.5 text-slate-500">&mdash;</td>}
                </tr>
                <tr className="bg-slate-950/30">
                  <td className="p-3.5 font-sans font-medium text-white">Synthesis LLM</td>
                  {comparison.runs.map((run) => (
                    <td key={run.id} className="p-3.5 text-slate-400">
                      {run.configuration_snapshot?.llm_model || 'local'}
                    </td>
                  ))}
                  {comparison.runs.length > 1 && <td className="p-3.5 text-slate-500">&mdash;</td>}
                </tr>

                {/* Performance Metrics */}
                {comparison.metric_keys.map((metric) => {
                  const deltaB =
                    comparison.runs.length > 1
                      ? comparison.deltas[comparison.runs[1].id]?.[metric]
                      : null;

                  return (
                    <tr key={metric} className="hover:bg-slate-800/20">
                      <td className="p-3.5 font-sans font-medium text-white capitalize">
                        {metric.replace('_', ' ')}
                      </td>
                      {comparison.runs.map((run) => {
                        const val = comparison.matrix[run.id]?.[metric];
                        return (
                          <td key={run.id} className="p-3.5 font-semibold text-slate-200">
                            {val != null ? (metric.includes('latency') ? `${val.toFixed(1)}ms` : val.toFixed(3)) : '--'}
                          </td>
                        );
                      })}
                      {comparison.runs.length > 1 && (
                        <td className="p-3.5">
                          {deltaB != null ? (
                            <span
                              className={`inline-flex items-center gap-1 font-bold ${
                                metric.includes('latency')
                                  ? deltaB < 0
                                    ? 'text-emerald-400'
                                    : 'text-rose-400'
                                  : deltaB > 0
                                  ? 'text-emerald-400'
                                  : deltaB < 0
                                  ? 'text-rose-400'
                                  : 'text-slate-400'
                              }`}
                            >
                              {deltaB > 0 ? (
                                <TrendingUp className="w-3.5 h-3.5" />
                              ) : deltaB < 0 ? (
                                <TrendingDown className="w-3.5 h-3.5" />
                              ) : (
                                <Minus className="w-3.5 h-3.5" />
                              )}
                              {deltaB > 0 ? `+${deltaB}` : deltaB}
                            </span>
                          ) : (
                            <span className="text-slate-500">--</span>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
