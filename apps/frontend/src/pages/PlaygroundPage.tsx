import React, { useState } from 'react';
import {
  Send,
  Layers,
  Sliders,
  Sparkles,
  BookOpen,
  Zap,
  Tag,
  AlertCircle,
  Hash,
  Clock,
  Layers3
} from 'lucide-react';
import { getAuthHeaders, getActiveProject } from '../lib/auth';

interface ChunkResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  text: string;
  dense_score: number;
  sparse_score: number;
  rrf_score: number;
  rerank_score?: number | null;
  initial_rank: number;
  reranked_rank?: number | null;
  metadata?: Record<string, any>;
}

interface CitationResult {
  citation_id: number;
  chunk_id: string;
  document_id: string;
  filename: string;
  dense_score: number;
  sparse_score: number;
  rerank_score?: number | null;
  preview: string;
}

interface QueryResponseData {
  answer: string;
  sources: CitationResult[];
  retrieved_chunks: ChunkResult[];
  scores: Record<string, any>;
  trace_id: string;
  latency_ms: number;
  tokens: {
    input_tokens?: number;
    output_tokens?: number;
    total_tokens?: number;
  };
}

export const PlaygroundPage: React.FC = () => {
  const activeProj = getActiveProject();
  const [query, setQuery] = useState('What database does AVOM use for vector search and metadata?');
  const [isSearching, setIsSearching] = useState(false);
  const [retrievalType, setRetrievalType] = useState<'hybrid' | 'dense' | 'sparse'>('hybrid');
  const [topK, setTopK] = useState(10);
  const [useReranker, setUseReranker] = useState(true);
  const [rerankTopK, setRerankTopK] = useState(6);
  const [finalContextK, setFinalContextK] = useState(3);
  const [llmModel, setLlmModel] = useState('local-deterministic');
  const [temperature, setTemperature] = useState(0.0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Response state initialized with sample data for immediate visual reference
  const [responseData, setResponseData] = useState<QueryResponseData>({
    answer:
      'AVOM utilizes PostgreSQL for structured metadata, user authentication, and project workspace isolation [1]. For high-dimensional dense vector embeddings and similarity search, AVOM integrates Qdrant [2]. Reciprocal Rank Fusion seamlessly unifies dense vector hits with sparse BM25 keyword matching.',
    sources: [
      {
        citation_id: 1,
        chunk_id: 'chk-init-01',
        document_id: 'doc-init-01',
        filename: 'architecture_spec.md',
        dense_score: 0.892,
        sparse_score: 0.741,
        rerank_score: 0.965,
        preview: 'PostgreSQL provides ACID compliance for project boundaries and ingestion metadata.'
      },
      {
        citation_id: 2,
        chunk_id: 'chk-init-02',
        document_id: 'doc-init-02',
        filename: 'vector_search.md',
        dense_score: 0.915,
        sparse_score: 0.684,
        rerank_score: 0.942,
        preview: 'Qdrant vector engine powers cosine distance dense ANN indexing.'
      }
    ],
    retrieved_chunks: [
      {
        chunk_id: 'chk-init-01',
        document_id: 'doc-init-01',
        filename: 'architecture_spec.md',
        text: 'PostgreSQL is the primary relational database in AVOM, storing all multi-tenant project records, user authentication hashes, document parsing logs, and evaluation metrics.',
        dense_score: 0.892,
        sparse_score: 0.741,
        rrf_score: 0.032,
        rerank_score: 0.965,
        initial_rank: 1,
        reranked_rank: 1,
        metadata: { chunk_index: 0 }
      },
      {
        chunk_id: 'chk-init-02',
        document_id: 'doc-init-02',
        filename: 'vector_search.md',
        text: 'Dense vector search in AVOM is delegated to Qdrant, handling cosine distance similarity lookups across chunk embeddings with project tenant filtering.',
        dense_score: 0.915,
        sparse_score: 0.684,
        rrf_score: 0.031,
        rerank_score: 0.942,
        initial_rank: 2,
        reranked_rank: 2,
        metadata: { chunk_index: 1 }
      }
    ],
    scores: {},
    trace_id: 'trc-demo-8f92b7',
    latency_ms: 324.5,
    tokens: {
      input_tokens: 380,
      output_tokens: 72,
      total_tokens: 452
    }
  });

  const handleRunQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setErrorMsg(null);

    try {
      const payload = {
        project_id: activeProj.id,
        query: query.trim(),
        configuration: {
          retrieval_type: retrievalType,
          top_k: topK,
          reranking: useReranker,
          rerank_top_k: rerankTopK,
          final_context_k: finalContextK,
          llm_model: llmModel,
          temperature: temperature
        }
      };

      const res = await fetch('/api/v1/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Query failed with status ${res.status}`);
      }

      const data: QueryResponseData = await res.json();
      setResponseData(data);
    } catch (err: any) {
      console.error('Playground query error:', err);
      setErrorMsg(
        err.message || 'Failed to query pipeline. Check that documents are uploaded in this workspace.'
      );
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="h-[calc(100vh-7.5rem)] flex gap-6 overflow-hidden max-w-7xl mx-auto">
      {/* Configuration Sidebar */}
      <div className="w-84 rounded-xl bg-slate-900/80 border border-slate-800 p-4 flex flex-col shrink-0 overflow-y-auto space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Pipeline Config</h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
            {activeProj.name}
          </span>
        </div>

        {/* Retrieval Method */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-300">Retrieval Strategy</label>
          <select
            value={retrievalType}
            onChange={(e) => setRetrievalType(e.target.value as any)}
            className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="hybrid">Hybrid (Dense Vector + BM25 Sparse)</option>
            <option value="dense">Dense Vector Only (Qdrant)</option>
            <option value="sparse">Sparse BM25 Keyword Only</option>
          </select>
        </div>

        {/* Candidate Top-K */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-slate-300">Candidate Top-K</span>
            <span className="font-mono text-indigo-400">{topK}</span>
          </div>
          <input
            type="range"
            min="2"
            max="30"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value))}
            className="w-full accent-indigo-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Reranker Toggle */}
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-200">Cross-Encoder Reranker</span>
            <input
              type="checkbox"
              checked={useReranker}
              onChange={(e) => setUseReranker(e.target.checked)}
              className="accent-indigo-500 w-4 h-4 rounded"
            />
          </div>
          {useReranker && (
            <>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>Rerank Candidates</span>
                  <span className="font-mono text-slate-300">{rerankTopK}</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="20"
                  value={rerankTopK}
                  onChange={(e) => setRerankTopK(parseInt(e.target.value))}
                  className="w-full accent-indigo-500 bg-slate-800 h-1 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>Final Context (LLM)</span>
                  <span className="font-mono text-indigo-300">{finalContextK} chunks</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={finalContextK}
                  onChange={(e) => setFinalContextK(parseInt(e.target.value))}
                  className="w-full accent-indigo-500 bg-slate-800 h-1 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </>
          )}
        </div>

        {/* LLM Generation */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-300">LLM Generation Model</label>
          <select
            value={llmModel}
            onChange={(e) => setLlmModel(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="local-deterministic">Deterministic Local Engine</option>
            <option value="gpt-4o-mini">gpt-4o-mini (OpenAI)</option>
            <option value="gemini-1.5-flash">gemini-1.5-flash (Google)</option>
          </select>
        </div>

        {/* Temperature */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-slate-300">Temperature</span>
            <span className="font-mono text-indigo-400">{temperature.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full accent-indigo-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>

      {/* Main Execution Area */}
      <div className="flex-1 flex flex-col gap-4 overflow-hidden">
        {/* Error Notification */}
        {errorMsg && (
          <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl flex items-center gap-2.5 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="flex-1">{errorMsg}</span>
          </div>
        )}

        {/* Query Input */}
        <form onSubmit={handleRunQuery} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a technical or domain query over your documents..."
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 shadow-inner"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching}
            className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all shrink-0 cursor-pointer"
          >
            {isSearching ? <Zap className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {isSearching ? 'Retrieving & Generating...' : 'Execute RAG'}
          </button>
        </form>

        {/* Generated Answer & Citations */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div className="flex items-center gap-2 text-xs font-semibold text-white">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Grounded Response
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
              <span className="flex items-center gap-1 text-slate-300">
                <Clock className="w-3 h-3 text-slate-500" />
                {responseData.latency_ms.toFixed(1)}ms
              </span>
              <span className="flex items-center gap-1 text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
                <Hash className="w-3 h-3 text-indigo-400" />
                {responseData.tokens.input_tokens ?? 0} in &bull; {responseData.tokens.output_tokens ?? 0} out
              </span>
              <span className="text-[10px] text-slate-500">
                Trace: {responseData.trace_id.slice(0, 12)}...
              </span>
            </div>
          </div>

          <p className="text-sm text-slate-200 leading-relaxed font-sans selection:bg-indigo-500/30">
            {responseData.answer}
          </p>

          {responseData.sources.length > 0 && (
            <div className="pt-2 flex flex-wrap items-center gap-2 text-xs">
              <span className="text-[11px] text-slate-400 font-mono">Sources:</span>
              {responseData.sources.map((source) => (
                <div
                  key={source.citation_id}
                  className="inline-flex items-center gap-1.5 bg-slate-800/90 border border-slate-700/80 px-2.5 py-1 rounded-md text-[11px] text-slate-200 font-mono"
                  title={source.preview}
                >
                  <Tag className="w-3 h-3 text-indigo-400" />
                  [{source.citation_id}] {source.filename}
                  {source.rerank_score != null && (
                    <span className="text-emerald-400 font-semibold ml-1">
                      ({source.rerank_score.toFixed(3)})
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Retrieval Inspector */}
        <div className="flex-1 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col overflow-hidden">
          <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
            <div className="flex items-center gap-2 text-xs font-semibold text-white">
              <Layers className="w-4 h-4 text-indigo-400" />
              Retrieval Inspector ({responseData.retrieved_chunks.length} Ranked Chunks)
            </div>
            <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
              <Layers3 className="w-3.5 h-3.5 text-indigo-400" />
              <span>
                {retrievalType.toUpperCase()} &bull; {useReranker ? 'Reranked' : 'Rank Fusion'}
              </span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {responseData.retrieved_chunks.map((chunk, idx) => (
              <div
                key={chunk.chunk_id || idx}
                className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold text-[11px]">
                      #{chunk.reranked_rank ?? chunk.initial_rank ?? idx + 1}
                    </span>
                    <span className="font-medium text-white flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                      {chunk.filename}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 font-mono text-[11px]">
                    <span className="text-slate-400">
                      Dense: <strong className="text-slate-200">{chunk.dense_score.toFixed(3)}</strong>
                    </span>
                    <span className="text-slate-400">
                      BM25: <strong className="text-slate-200">{chunk.sparse_score.toFixed(3)}</strong>
                    </span>
                    <span className="text-slate-400">
                      RRF: <strong className="text-slate-200">{chunk.rrf_score.toFixed(4)}</strong>
                    </span>
                    {chunk.rerank_score != null && (
                      <span className="text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                        Reranker: <strong>{chunk.rerank_score.toFixed(3)}</strong>
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-xs text-slate-300 font-mono bg-slate-900/60 p-2.5 rounded border border-slate-800/60 leading-relaxed whitespace-pre-wrap">
                  "{chunk.text}"
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
