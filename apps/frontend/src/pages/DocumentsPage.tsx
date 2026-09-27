import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle,
  AlertCircle,
  Trash2,
  Layers,
  X,
  Sliders
} from 'lucide-react';
import { getAuthHeaders, getActiveProject } from '../lib/auth';

interface DocumentItem {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  checksum: string;
  status: string;
  chunk_count: number;
  embedding_model: string;
  chunking_strategy: string;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

interface ChunkItem {
  id: string;
  document_id: string;
  project_id: string;
  chunk_index: number;
  text_content: string;
  start_char: number;
  end_char: number;
  metadata_json: Record<string, any>;
  vector_id?: string | null;
  created_at: string;
}

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [activeProject, setActiveProjectState] = useState(getActiveProject());

  // Upload configuration
  const [chunkingStrategy, setChunkingStrategy] = useState('recursive');
  const [chunkSize, setChunkSize] = useState(500);
  const [chunkOverlap, setChunkOverlap] = useState(50);
  const [embeddingModel, setEmbeddingModel] = useState('bge-small-en-v1.5');
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Chunk inspection drawer
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [chunks, setChunks] = useState<ChunkItem[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    if (!activeProject.id || activeProject.id === 'default-proj') {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/documents?project_id=${activeProject.id}`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error('Failed to fetch documents', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    const handleProjChange = () => {
      const p = getActiveProject();
      setActiveProjectState(p);
    };
    window.addEventListener('avom_active_project_changed', handleProjChange);
    return () => {
      window.removeEventListener('avom_active_project_changed', handleProjChange);
    };
  }, [activeProject.id]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', activeProject.id);
    formData.append('chunking_strategy', chunkingStrategy);
    formData.append('chunk_size', chunkSize.toString());
    formData.append('chunk_overlap', chunkOverlap.toString());
    formData.append('embedding_model', embeddingModel);

    try {
      const res = await fetch('/api/v1/documents/upload', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Document ingestion failed');
      }

      const newDoc = await res.json();
      setDocuments([newDoc, ...documents]);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Error uploading file');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleInspectChunks = async (doc: DocumentItem) => {
    setSelectedDoc(doc);
    setLoadingChunks(true);
    try {
      const res = await fetch(`/api/v1/documents/${doc.id}/chunks`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setChunks(data);
      }
    } catch (err) {
      console.error('Failed to load chunks', err);
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleDeleteDoc = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this document and its vector embeddings?')) return;
    try {
      const res = await fetch(`/api/v1/documents/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        setDocuments(documents.filter((d) => d.id !== id));
        if (selectedDoc?.id === id) {
          setSelectedDoc(null);
        }
      }
    } catch (err) {
      console.error('Failed to delete document', err);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Document Ingestion & Chunks</h2>
          <p className="text-sm text-slate-400 mt-1">
            Ingest PDFs, TXT, Markdown, and DOCX files into workspace{' '}
            <span className="text-indigo-400 font-mono font-medium">"{activeProject.name}"</span>.
          </p>
        </div>
      </div>

      {uploadError && (
        <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{uploadError}</span>
          </div>
          <button onClick={() => setUploadError(null)} className="text-rose-400 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Upload & Pipeline Configuration Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Dropzone */}
        <div
          onClick={() => fileInputRef.current?.click()}
          className="lg:col-span-2 p-8 border-2 border-dashed border-slate-800 hover:border-indigo-500/60 rounded-xl bg-slate-900/40 text-center transition-all cursor-pointer flex flex-col items-center justify-center min-h-[220px]"
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            accept=".pdf,.txt,.md,.markdown,.docx,.doc"
            className="hidden"
          />
          <UploadCloud className={`w-10 h-10 ${uploading ? 'text-indigo-400 animate-bounce' : 'text-slate-500'} mb-3`} />
          <h3 className="text-sm font-semibold text-white">
            {uploading ? 'Parsing, Chunking & Generating Vector Embeddings...' : 'Drop documents here or click to browse'}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Supports PDF, Markdown (.md), Plain Text (.txt), and Word (.docx) up to 50MB
          </p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Strategy: {chunkingStrategy}
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Chunk Size: {chunkSize} chars
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Overlap: {chunkOverlap} chars
            </span>
          </div>
        </div>

        {/* Chunking & Embedding Parameters */}
        <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3.5">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
              Ingestion Parameters
            </h3>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-300">Chunking Strategy</label>
            <select
              value={chunkingStrategy}
              onChange={(e) => setChunkingStrategy(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="recursive">Recursive Character (Preserves Paragraphs)</option>
              <option value="fixed">Fixed-Size Window (Equal Chunks)</option>
              <option value="semantic">Semantic (Sentence & Thought Boundaries)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label className="text-[11px] text-slate-300 block mb-1">Target Size (chars)</label>
              <input
                type="number"
                min="50"
                max="3000"
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono text-xs"
              />
            </div>
            <div>
              <label className="text-[11px] text-slate-300 block mb-1">Overlap (chars)</label>
              <input
                type="number"
                min="0"
                max="500"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono text-xs"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-300">Embedding Model</label>
            <select
              value={embeddingModel}
              onChange={(e) => setEmbeddingModel(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="bge-small-en-v1.5">bge-small-en-v1.5 (384d, Fast)</option>
              <option value="text-embedding-3-small">text-embedding-3-small (1536d)</option>
              <option value="bge-large-en-v1.5">bge-large-en-v1.5 (1024d)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Document Corpus Table */}
      <div className="rounded-lg bg-slate-900/70 border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Ingested Corpus</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">Total: {documents.length}</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400 font-mono">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No documents ingested in this workspace yet. Upload files above to index knowledge.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="p-3.5">Filename</th>
                <th className="p-3.5">Type</th>
                <th className="p-3.5">Size</th>
                <th className="p-3.5">Strategy</th>
                <th className="p-3.5">Chunks</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {documents.map((doc) => (
                <tr
                  key={doc.id}
                  onClick={() => handleInspectChunks(doc)}
                  className="hover:bg-slate-800/40 transition-colors cursor-pointer"
                >
                  <td className="p-3.5 font-medium text-white flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                    <span className="truncate max-w-xs">{doc.filename}</span>
                  </td>
                  <td className="p-3.5 font-mono text-slate-400 uppercase">{doc.file_type}</td>
                  <td className="p-3.5 font-mono text-slate-400">{(doc.file_size / 1024).toFixed(1)} KB</td>
                  <td className="p-3.5 font-mono text-slate-400">{doc.chunking_strategy}</td>
                  <td className="p-3.5 font-mono text-slate-200">{doc.chunk_count} chunks</td>
                  <td className="p-3.5">
                    <span
                      className={`inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded border ${
                        doc.status === 'INDEXED'
                          ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40'
                          : 'text-amber-400 bg-amber-950/40 border-amber-800/40'
                      }`}
                    >
                      <CheckCircle className="w-3 h-3" /> {doc.status}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleInspectChunks(doc);
                        }}
                        className="text-indigo-400 hover:underline flex items-center gap-1 text-[11px]"
                      >
                        <Layers className="w-3 h-3" /> Inspect
                      </button>
                      <button
                        onClick={(e) => handleDeleteDoc(doc.id, e)}
                        className="text-slate-500 hover:text-rose-400 p-1 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Chunks Inspector Drawer / Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-3xl max-h-[85vh] flex flex-col relative shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <div>
                  <h3 className="text-sm font-semibold text-white">{selectedDoc.filename}</h3>
                  <p className="text-[11px] text-slate-400 font-mono">
                    {selectedDoc.chunk_count} Chunks &bull; Strategy: {selectedDoc.chunking_strategy} &bull; Model:{' '}
                    {selectedDoc.embedding_model}
                  </p>
                </div>
              </div>
              <button onClick={() => setSelectedDoc(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {loadingChunks ? (
                <div className="text-center text-xs text-slate-400 font-mono py-8">Loading chunk payload...</div>
              ) : chunks.length === 0 ? (
                <div className="text-center text-xs text-slate-400 py-8">No chunks found for this document.</div>
              ) : (
                chunks.map((chk) => (
                  <div key={chk.id} className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold text-[11px]">
                          Chunk #{chk.chunk_index + 1}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          Chars: [{chk.start_char}..{chk.end_char}] ({chk.end_char - chk.start_char} chars)
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                        Vector Indexed
                      </span>
                    </div>
                    <p className="text-xs text-slate-200 font-mono bg-slate-900/60 p-2.5 rounded border border-slate-800/60 leading-relaxed whitespace-pre-wrap">
                      {chk.text_content}
                    </p>
                    {chk.metadata_json && Object.keys(chk.metadata_json).length > 0 && (
                      <div className="text-[10px] font-mono text-slate-400 flex items-center gap-2">
                        <span>Metadata:</span>
                        <code className="text-slate-300 bg-slate-800/50 px-1.5 py-0.5 rounded">
                          {JSON.stringify(chk.metadata_json)}
                        </code>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
