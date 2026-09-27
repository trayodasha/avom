import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  FileText,
  Database,
  Terminal,
  CheckCircle2,
  GitCompare,
  Activity,
  Settings as SettingsIcon,
  ShieldCheck,
  Cpu,
  User as UserIcon,
  LogIn,
  LogOut,
  X
} from 'lucide-react';
import { getStoredAuth, setStoredAuth, clearStoredAuth, getActiveProject, User } from '../lib/auth';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderGit2 },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'RAG Playground', href: '/playground', icon: Terminal },
  { name: 'Evaluations', href: '/evaluations', icon: CheckCircle2 },
  { name: 'Experiments', href: '/experiments', icon: GitCompare },
  { name: 'Traces', href: '/traces', icon: Activity },
  { name: 'Settings', href: '/settings', icon: SettingsIcon },
];

export const Layout: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeWorkspace, setActiveWorkspace] = useState(getActiveProject());
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'USER' | 'ADMIN'>('USER');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const { user } = getStoredAuth();
    if (user) {
      setCurrentUser(user);
    } else {
      // Default initial mock active user for UX convenience if none stored
      const demoUser: User = {
        id: 'usr-demo-01',
        email: 'engineer@avom.ai',
        full_name: 'Lead AI Engineer',
        role: 'ADMIN',
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setStoredAuth('demo-jwt-token-active', demoUser);
      setCurrentUser(demoUser);
    }

    const handleProjectChange = () => {
      setActiveWorkspace(getActiveProject());
    };
    window.addEventListener('avom_active_project_changed', handleProjectChange);
    return () => {
      window.removeEventListener('avom_active_project_changed', handleProjectChange);
    };
  }, []);

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      if (isRegistering) {
        const res = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, full_name: fullName, role }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Registration failed');
        }
        // Auto login after registration
        const loginRes = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        const data = await loginRes.json();
        setStoredAuth(data.access_token, data.user);
        setCurrentUser(data.user);
      } else {
        const loginRes = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        if (!loginRes.ok) {
          const err = await loginRes.json();
          throw new Error(err.detail || 'Invalid email or password');
        }
        const data = await loginRes.json();
        setStoredAuth(data.access_token, data.user);
        setCurrentUser(data.user);
      }
      setShowAuthModal(false);
      setEmail('');
      setPassword('');
      setFullName('');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearStoredAuth();
    setCurrentUser(null);
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/60 backdrop-blur-md flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              <Cpu className="w-5 h-5 text-indigo-100" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
                AVOM
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  RAG Core
                </span>
              </h1>
              <p className="text-[11px] text-slate-400 font-mono">Evaluation-First RAG</p>
            </div>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
            Platform Engine
          </div>
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Card & System Status */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-900/40 space-y-2">
          {currentUser ? (
            <div className="flex items-center justify-between p-2 rounded bg-slate-800/50 border border-slate-700/60 text-xs">
              <div className="flex items-center gap-2 overflow-hidden">
                <div className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300 flex items-center justify-center font-bold text-[10px] shrink-0">
                  {currentUser.email.slice(0, 2).toUpperCase()}
                </div>
                <div className="truncate">
                  <div className="text-slate-200 font-medium truncate text-[11px]">
                    {currentUser.full_name || currentUser.email}
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-[9px] font-mono uppercase px-1 py-0.2 rounded bg-indigo-500/20 text-indigo-300">
                      {currentUser.role}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={handleLogout}
                title="Log Out"
                className="text-slate-400 hover:text-rose-400 p-1 rounded transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-medium transition-all"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Log In / Sign Up</span>
            </button>
          )}

          <div className="flex items-center justify-between text-xs px-2 py-1.5 rounded bg-slate-800/40 border border-slate-700/50">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-300 text-[11px]">System Ready</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">v1.0.0</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-slate-950">
        <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between shrink-0 bg-slate-900/30 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <span>Workspace:</span>
            <span className="text-slate-200 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 font-medium">
              {activeWorkspace.name}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-2.5 py-1 rounded-full">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Strict Groundedness</span>
            </div>
            {currentUser && (
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Role: {currentUser.role}
              </span>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </div>
      </main>

      {/* Auth Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md p-6 relative shadow-2xl">
            <button
              onClick={() => setShowAuthModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="p-2 rounded-lg bg-indigo-600 text-white">
                <UserIcon className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  {isRegistering ? 'Create AVOM Account' : 'Welcome Back'}
                </h3>
                <p className="text-xs text-slate-400">
                  {isRegistering
                    ? 'Register as an engineer or admin to manage RAG evaluations'
                    : 'Sign in to access your workspaces and evaluation benchmarks'}
                </p>
              </div>
            </div>

            {errorMsg && (
              <div className="mb-4 p-2.5 rounded bg-rose-950/50 border border-rose-800/60 text-rose-300 text-xs">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="space-y-3">
              {isRegistering && (
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Ada Lovelace"
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              )}

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="engineer@avom.ai"
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              {isRegistering && (
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Role</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as 'USER' | 'ADMIN')}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="USER">USER (Query, Ingest, View Evals)</option>
                    <option value="ADMIN">ADMIN (Workspace Management, Full Privileges)</option>
                  </select>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
              >
                {loading ? 'Authenticating...' : isRegistering ? 'Register Account' : 'Sign In'}
              </button>
            </form>

            <div className="mt-4 pt-3 border-t border-slate-800 text-center">
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(!isRegistering);
                  setErrorMsg(null);
                }}
                className="text-xs text-indigo-400 hover:underline"
              >
                {isRegistering
                  ? 'Already have an account? Sign In'
                  : "Don't have an account? Create one"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
