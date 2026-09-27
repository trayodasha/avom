import React, { useState, useEffect } from 'react';
import { Activity, AlertCircle } from 'lucide-react';
import { getAuthHeaders, getActiveProject } from '../lib/auth';

interface SpanData {
  name: string;
  start_time_ms: number;
  end_time_ms: number;
  duration_ms: number;
  attributes?: Record<string, any>;
}

interface TraceRecord {
  id: string;
  project_id: string;
  user_id?: string | null;
  query: string;
  answer?: string | null;
  status: string;
  total_latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  configuration_json: Record<string, any>;
  spans_json: SpanData[];
  created_at: string;
}

export const TracesPage: React.FC = () => {
  const activeProj = getActiveProject();
  const [traces, setTraces] = useState<TraceRecord[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<TraceRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchTraces = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/traces?project_id=${activeProj.id}&limit=30`, {
          headers: getAuthHeaders(),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: TraceRecord[] = await res.json();
        setTraces(data);
        if (data.length > 0) {
          setSelectedTrace(data[0]);
        }
      } catch (err: any) {
        console.error(err);
        setErrorMsg('Failed to load traces for this project.');
      } finally {
        setLoading(false);
      }
    };
    fetchTraces();
  }, [activeProj.id]);

  const spanColors: Record<string, string> = {
    hybrid_retrieval: 'bg-indigo-500',
    dense_retrieval: 'bg-sky-500',
    sparse_retrieval: 'bg-cyan-500',
    cross_encoder_rerank: 'bg-violet-500',
    prompt_construction: 'bg-amber-500',
    llm_synthesis: 'bg-emerald-500',
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Observability & Pipeline Traces</h2>
          <p className="text-sm text-slate-400 mt-1">
            OpenTelemetry-compatible latency profiling across query embedding, hybrid retrieval, cross-encoder reranking, and LLM synthesis.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl flex items-center gap-2 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Traces List */}
        <div className="rounded-xl bg-slate-900/80 border border-slate-800 overflow-hidden flex flex-col h-[calc(100vh-14rem)]">
          <div className="p-3.5 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Recent Execution Traces</span>
            <span className="text-[11px] font-mono text-slate-400">{traces.length} Traces</span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/70">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading traces...</div>
            ) : traces.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No query traces logged yet. Execute queries in the Playground or run Evaluations to generate traces.
              </div>
            ) : (
              traces.map((t) => {
                const isSelected = selectedTrace?.id === t.id;
                return (
                  <div
                    key={t.id}
                    onClick={() => setSelectedTrace(t)}
                    className={`p-3.5 cursor-pointer transition-colors space-y-1.5 ${
                      isSelected
                        ? 'bg-indigo-600/15 border-l-2 border-indigo-500'
                        : 'hover:bg-slate-800/30'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-[11px] text-slate-400">
                        {t.id.slice(0, 14)}...
                      </span>
                      <span className="font-mono text-emerald-400 text-[11px]">
                        {t.total_latency_ms.toFixed(1)}ms
                      </span>
                    </div>
                    <p className="text-xs text-slate-200 font-medium line-clamp-1">
                      {t.query}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                      <span>{t.configuration_json?.retrieval_type || 'hybrid'}</span>
                      <span>&bull;</span>
                      <span>{t.input_tokens + t.output_tokens} tokens</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Selected Trace Waterfall View */}
        <div className="lg:col-span-2 rounded-xl bg-slate-900/80 border border-slate-800 overflow-hidden flex flex-col h-[calc(100vh-14rem)]">
          {selectedTrace ? (
            <>
              {/* Header */}
              <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-indigo-400" />
                    <h3 className="text-sm font-semibold text-white font-mono">
                      Trace: {selectedTrace.id}
                    </h3>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                    "{selectedTrace.query}"
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className="text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded">
                    {selectedTrace.total_latency_ms.toFixed(1)}ms Total
                  </span>
                  <span className="text-slate-300 bg-slate-800/80 px-2 py-0.5 rounded">
                    {selectedTrace.input_tokens + selectedTrace.output_tokens} Tokens
                  </span>
                </div>
              </div>

              {/* Waterfall Spans */}
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                <div>
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                    Waterfall Execution Timeline
                  </h4>

                  <div className="space-y-4">
                    {selectedTrace.spans_json && selectedTrace.spans_json.length > 0 ? (
                      selectedTrace.spans_json.map((span, idx) => {
                        const total = selectedTrace.total_latency_ms || 1.0;
                        const widthPct = Math.max(5, Math.min(100, (span.duration_ms / total) * 100));
                        const leftPct = Math.min(95, (span.start_time_ms / total) * 100);
                        const colorClass = spanColors[span.name] || 'bg-indigo-500';

                        return (
                          <div key={span.name || idx} className="space-y-1.5">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-mono text-slate-200">
                                {idx + 1}. {span.name}
                              </span>
                              <div className="flex items-center gap-2 font-mono text-[11px]">
                                <span className="text-indigo-400 font-bold">
                                  {span.duration_ms.toFixed(1)}ms
                                </span>
                                <span className="text-slate-500">
                                  ({Math.round((span.duration_ms / total) * 100)}%)
                                </span>
                              </div>
                            </div>

                            <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-slate-800/80 relative">
                              <div
                                className={`h-full rounded-full ${colorClass} transition-all`}
                                style={{
                                  width: `${widthPct}%`,
                                  marginLeft: `${leftPct}%`,
                                }}
                              />
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-xs text-slate-400 italic">No child spans recorded for this trace.</div>
                    )}
                  </div>
                </div>

                {/* Synthesis Output Preview */}
                {selectedTrace.answer && (
                  <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                    <span className="text-xs font-semibold text-slate-300 block">Synthesized Response</span>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">
                      {selectedTrace.answer}
                    </p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-xs text-slate-400 m-auto">
              Select a trace from the left panel to inspect its waterfall timeline.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
