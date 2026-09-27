import React from 'react';
import { Key, Database } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="pb-2 border-b border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-white">System Settings & Providers</h2>
        <p className="text-sm text-slate-400 mt-1">
          Configure API credentials, vector storage parameters, database pooling, and caching layer.
        </p>
      </div>

      <div className="space-y-4">
        <div className="p-5 rounded-lg bg-slate-900/70 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Key className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">LLM & Embedding Providers</h3>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">OpenAI API Key</label>
              <input
                type="password"
                placeholder="sk-..."
                defaultValue="••••••••••••••••••••••••••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">Google Gemini API Key</label>
              <input
                type="password"
                placeholder="AIza..."
                className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>
        </div>

        <div className="p-5 rounded-lg bg-slate-900/70 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Database className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Infrastructure Endpoints</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="font-medium text-slate-300 block mb-1">Qdrant Host</label>
              <input
                type="text"
                defaultValue="http://localhost:6333"
                className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-slate-200 font-mono"
              />
            </div>
            <div>
              <label className="font-medium text-slate-300 block mb-1">Redis URL</label>
              <input
                type="text"
                defaultValue="redis://localhost:6379/0"
                className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-slate-200 font-mono"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
