import React, { useState, useEffect } from 'react';
import { Plus, CheckSquare, Trash2, Eye, X, BookOpen, AlertCircle } from 'lucide-react';
import { getAuthHeaders, getActiveProject } from '../lib/auth';

interface EvaluationDataset {
  id: string;
  project_id: string;
  name: string;
  description?: string | null;
  example_count: number;
  created_at: string;
  updated_at: string;
}

interface EvaluationExample {
  id: string;
  dataset_id: string;
  project_id: string;
  query: string;
  ground_truth: string;
  ground_truth_context?: string | null;
  created_at: string;
}

export const DatasetsPage: React.FC = () => {
  const activeProj = getActiveProject();
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDatasetName, setNewDatasetName] = useState('');
  const [newDatasetDesc, setNewDatasetDesc] = useState('');

  // Selected dataset for viewing/adding examples
  const [selectedDataset, setSelectedDataset] = useState<EvaluationDataset | null>(null);
  const [examples, setExamples] = useState<EvaluationExample[]>([]);
  const [examplesLoading, setExamplesLoading] = useState(false);
  const [showAddExampleModal, setShowAddExampleModal] = useState(false);
  const [exQuery, setExQuery] = useState('');
  const [exGroundTruth, setExGroundTruth] = useState('');
  const [exContext, setExContext] = useState('');

  const fetchDatasets = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`/api/v1/datasets?project_id=${activeProj.id}`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDatasets(data);
    } catch (err: any) {
      console.error(err);
      setErrorMsg('Failed to load datasets for this project.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, [activeProj.id]);

  const handleCreateDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDatasetName.trim()) return;

    try {
      const res = await fetch('/api/v1/datasets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          project_id: activeProj.id,
          name: newDatasetName.trim(),
          description: newDatasetDesc.trim() || undefined,
        }),
      });

      if (!res.ok) throw new Error('Failed to create dataset');
      setShowCreateModal(false);
      setNewDatasetName('');
      setNewDatasetDesc('');
      await fetchDatasets();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error creating dataset');
    }
  };

  const handleOpenExamples = async (dataset: EvaluationDataset) => {
    setSelectedDataset(dataset);
    setExamplesLoading(true);
    try {
      const res = await fetch(`/api/v1/datasets/${dataset.id}/examples`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error('Failed to fetch examples');
      const data = await res.json();
      setExamples(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setExamplesLoading(false);
    }
  };

  const handleAddExample = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDataset || !exQuery.trim() || !exGroundTruth.trim()) return;

    try {
      const res = await fetch(`/api/v1/datasets/${selectedDataset.id}/examples`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          examples: [
            {
              query: exQuery.trim(),
              ground_truth: exGroundTruth.trim(),
              ground_truth_context: exContext.trim() || undefined,
            },
          ],
        }),
      });

      if (!res.ok) throw new Error('Failed to add example');
      setShowAddExampleModal(false);
      setExQuery('');
      setExGroundTruth('');
      setExContext('');
      await handleOpenExamples(selectedDataset);
      await fetchDatasets();
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleDeleteDataset = async (datasetId: string) => {
    if (!window.confirm('Delete this evaluation dataset?')) return;
    try {
      const res = await fetch(`/api/v1/datasets/${datasetId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error('Failed to delete dataset');
      if (selectedDataset?.id === datasetId) {
        setSelectedDataset(null);
      }
      await fetchDatasets();
    } catch (err: any) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Gold Standard Evaluation Datasets</h2>
          <p className="text-sm text-slate-400 mt-1">
            Curate test sets with ground truth answers for precision/recall and faithfulness benchmarking in workspace <strong className="text-indigo-300 font-mono">[{activeProj.name}]</strong>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" /> New Dataset
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl flex items-center gap-2 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Datasets Grid */}
      {loading ? (
        <div className="p-12 text-center text-sm text-slate-400">Loading datasets...</div>
      ) : datasets.length === 0 ? (
        <div className="p-12 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
          <BookOpen className="w-8 h-8 text-slate-500 mx-auto" />
          <h4 className="text-sm font-semibold text-white">No Evaluation Datasets Created</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Create an evaluation dataset with question and ground-truth pairs to benchmark retrieval recall and LLM faithfulness.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-2 inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-medium"
          >
            <Plus className="w-3.5 h-3.5" /> Create First Dataset
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {datasets.map((ds) => (
            <div
              key={ds.id}
              className={`p-5 rounded-xl border transition-all space-y-4 ${
                selectedDataset?.id === ds.id
                  ? 'bg-slate-900 border-indigo-500/80 shadow-lg shadow-indigo-500/10'
                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                  {ds.example_count} {ds.example_count === 1 ? 'EXAMPLE' : 'EXAMPLES'}
                </span>
                <button
                  onClick={() => handleDeleteDataset(ds.id)}
                  className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                  title="Delete Dataset"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div>
                <h3 className="text-base font-semibold text-white">{ds.name}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                  {ds.description || 'No description provided.'}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-1">
                  <CheckSquare className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Ground Truth QA</span>
                </div>
                <button
                  onClick={() => handleOpenExamples(ds)}
                  className="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 cursor-pointer"
                >
                  <Eye className="w-3.5 h-3.5" /> View & Add QA &rarr;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Examples Drawer */}
      {selectedDataset && (
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <span>QA Examples: {selectedDataset.name}</span>
                <span className="text-xs font-mono text-slate-400 font-normal">({examples.length} total)</span>
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowAddExampleModal(true)}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Add QA Pair
              </button>
              <button
                onClick={() => setSelectedDataset(null)}
                className="p-1.5 text-slate-400 hover:text-white rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {examplesLoading ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading examples...</div>
          ) : examples.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400">
              No QA examples in this dataset yet. Click <strong>Add QA Pair</strong> to add test queries and ground truth answers.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {examples.map((ex, idx) => (
                <div key={ex.id || idx} className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-indigo-400 font-semibold">#{idx + 1} Question:</span>
                    <span className="text-[10px] text-slate-500 font-mono">{ex.id.slice(0, 8)}</span>
                  </div>
                  <p className="text-xs text-white font-medium">{ex.query}</p>
                  <div className="text-[11px] bg-slate-900/80 p-2.5 rounded border border-slate-800/80 space-y-1">
                    <div className="text-slate-400 font-mono text-[10px]">Reference Ground Truth Answer:</div>
                    <div className="text-slate-200">{ex.ground_truth}</div>
                    {ex.ground_truth_context && (
                      <div className="text-slate-400 text-[10px] pt-1 border-t border-slate-800/60 italic">
                        Context: {ex.ground_truth_context}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal: Create Dataset */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-semibold text-white">Create Evaluation Dataset</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreateDataset} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300">Dataset Name *</label>
                <input
                  type="text"
                  required
                  value={newDatasetName}
                  onChange={(e) => setNewDatasetName(e.target.value)}
                  placeholder="e.g. Architecture Benchmark Suite"
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300">Description</label>
                <textarea
                  rows={3}
                  value={newDatasetDesc}
                  onChange={(e) => setNewDatasetDesc(e.target.value)}
                  placeholder="Purpose of this evaluation test suite..."
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold"
                >
                  Create Dataset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add QA Example */}
      {showAddExampleModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-semibold text-white">Add Ground Truth QA Pair</h3>
              <button onClick={() => setShowAddExampleModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleAddExample} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300">Question / Query *</label>
                <input
                  type="text"
                  required
                  value={exQuery}
                  onChange={(e) => setExQuery(e.target.value)}
                  placeholder="e.g. What database is used for vector search?"
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300">Ground Truth Answer *</label>
                <textarea
                  rows={2}
                  required
                  value={exGroundTruth}
                  onChange={(e) => setExGroundTruth(e.target.value)}
                  placeholder="The canonical correct answer..."
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300">Reference Ground Truth Context (Optional)</label>
                <textarea
                  rows={2}
                  value={exContext}
                  onChange={(e) => setExContext(e.target.value)}
                  placeholder="Passage or document excerpt..."
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddExampleModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold"
                >
                  Save QA Pair
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
