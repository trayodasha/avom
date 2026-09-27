import React, { useState, useEffect } from 'react';
import { Plus, ArrowRight, Trash2, Check, FolderGit2, X } from 'lucide-react';
import { getAuthHeaders, getActiveProject, setActiveProject, Project } from '../lib/auth';

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeProject, setLocalActiveProject] = useState(getActiveProject());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/projects', {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (data.length > 0 && activeProject.id === 'default-proj') {
          setActiveProject(data[0].id, data[0].name);
          setLocalActiveProject({ id: data[0].id, name: data[0].name });
        }
      }
    } catch (err) {
      console.error('Failed to fetch projects', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    try {
      const res = await fetch('/api/v1/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ name, description }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create project');
      }
      const newProj = await res.json();
      setProjects([newProj, ...projects]);
      setActiveProject(newProj.id, newProj.name);
      setLocalActiveProject({ id: newProj.id, name: newProj.name });
      setShowCreateModal(false);
      setName('');
      setDescription('');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Error creating project');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteProject = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this project workspace?')) return;
    try {
      const res = await fetch(`/api/v1/projects/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const remaining = projects.filter((p) => p.id !== id);
        setProjects(remaining);
        if (activeProject.id === id && remaining.length > 0) {
          setActiveProject(remaining[0].id, remaining[0].name);
          setLocalActiveProject({ id: remaining[0].id, name: remaining[0].name });
        }
      }
    } catch (err) {
      console.error('Failed to delete project', err);
    }
  };

  const handleSelectWorkspace = (proj: Project) => {
    setActiveProject(proj.id, proj.name);
    setLocalActiveProject({ id: proj.id, name: proj.name });
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Project Workspaces</h2>
          <p className="text-sm text-slate-400 mt-1">
            Isolate document corpora, retrieval configurations, and evaluation benchmarks per project.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          New Project
        </button>
      </div>

      {loading ? (
        <div className="text-xs text-slate-400 font-mono py-8 text-center">Loading workspaces...</div>
      ) : projects.length === 0 ? (
        <div className="p-12 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
          <FolderGit2 className="w-10 h-10 text-slate-500 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-white">No projects created yet</h3>
          <p className="text-xs text-slate-400 mt-1 mb-4">
            Create an isolated project workspace to begin ingesting documents and running evaluations.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold"
          >
            Create Your First Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((proj) => {
            const isActive = activeProject.id === proj.id;
            return (
              <div
                key={proj.id}
                onClick={() => handleSelectWorkspace(proj)}
                className={`p-5 rounded-lg bg-slate-900/70 border transition-all flex flex-col justify-between cursor-pointer ${
                  isActive
                    ? 'border-indigo-500 shadow-md shadow-indigo-500/10'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    {isActive ? (
                      <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                        <Check className="w-3 h-3" /> ACTIVE WORKSPACE
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        WORKSPACE
                      </span>
                    )}
                    <button
                      onClick={(e) => handleDeleteProject(proj.id, e)}
                      title="Delete Project"
                      className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <h3 className="text-base font-semibold text-white">{proj.name}</h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                    {proj.description || 'No description provided.'}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-400 font-mono text-[10px]">
                    Created: {new Date(proj.created_at).toLocaleDateString()}
                  </span>
                  <span className="text-indigo-400 font-medium flex items-center gap-1 hover:underline">
                    {isActive ? 'Current' : 'Select'} <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md p-6 relative shadow-2xl">
            <button
              onClick={() => setShowCreateModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="p-2 rounded-lg bg-indigo-600 text-white">
                <FolderGit2 className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Create New Workspace</h3>
                <p className="text-xs text-slate-400">
                  Define an isolated environment for knowledge ingestion and RAG benchmarking.
                </p>
              </div>
            </div>

            {errorMsg && (
              <div className="mb-4 p-2.5 rounded bg-rose-950/50 border border-rose-800/60 text-rose-300 text-xs">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleCreateProject} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Financial Reports 2026"
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Description</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Internal audit documents and 10-K quarterly filings..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-2 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
              >
                {submitting ? 'Creating Workspace...' : 'Create Workspace'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
