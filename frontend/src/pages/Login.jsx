import React, { useState } from 'react';
import { Snowflake, ShieldCheck, Database, Key, LayoutGrid, Search } from 'lucide-react';
import { connectToSnowflake, loadSession } from '../api/api';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';

const Login = () => {
    const [isLoadMode, setIsLoadMode] = useState(false);
    const [credentials, setCredentials] = useState({ account: '', username: '', password: '', warehouse: 'COMPUTE_WH', role: 'ACCOUNTADMIN' });
    const [sessionId, setSessionId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { setSession } = useAuth();

    const handleConnect = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const data = await connectToSnowflake(credentials);
            setSession(data);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    };

    const handleLoad = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const data = await loadSession(sessionId);
            setSession(data);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-[#080e1a] relative overflow-hidden">
            {/* Background Orbs */}
            <div className="absolute top-[-10%] right-[-10%] w-[400px] h-[400px] bg-primary/20 rounded-full blur-[120px]"></div>
            <div className="absolute bottom-[-10%] left-[-10%] w-[350px] h-[350px] bg-secondary/15 rounded-full blur-[100px]"></div>

            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-lg relative z-10"
            >
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-primary/10 border border-primary/20 backdrop-blur-xl mb-6">
                        <Snowflake className="w-10 h-10 text-primary-light" strokeWidth={1.5} />
                    </div>
                    <h1 className="text-4xl font-extrabold tracking-tight text-white mb-3">
                        Snow<span className="text-primary-light">Advisor</span>
                    </h1>
                    <p className="text-text-muted text-lg">Premium Snowflake Cost Intelligence Dashboard</p>
                </div>

                <div className="glass-card p-1">
                    <div className="flex bg-sidebar/50 rounded-lg p-1 mb-6">
                        <button 
                            className={`flex-1 py-2 px-4 rounded-md text-sm font-semibold transition-all ${!isLoadMode ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-text-muted hover:text-text'}`}
                            onClick={() => setIsLoadMode(false)}
                        >
                            New Connection
                        </button>
                        <button 
                            className={`flex-1 py-2 px-4 rounded-md text-sm font-semibold transition-all ${isLoadMode ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-text-muted hover:text-text'}`}
                            onClick={() => setIsLoadMode(true)}
                        >
                            Past Session
                        </button>
                    </div>

                    <div className="p-6">
                        {error && (
                            <div className="mb-6 p-4 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm flex items-start gap-3">
                                <div className="p-1 rounded-md bg-danger/10">⚠️</div>
                                <p className="leading-relaxed">{typeof error === 'string' ? error : JSON.stringify(error)}</p>
                            </div>
                        )}

                        {!isLoadMode ? (
                            <form onSubmit={handleConnect} className="space-y-5">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-text-muted uppercase tracking-wider">Account Identifier</label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-primary transition-colors text-text-muted">
                                            <Database className="w-4.5 h-4.5" />
                                        </div>
                                        <input 
                                            required
                                            className="w-full bg-[#0f1a2e] border border-border rounded-xl py-3 pl-10 pr-4 text-white focus:outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-text-muted/40"
                                            placeholder="abc12345.us-east-1"
                                            value={credentials.account}
                                            onChange={(e) => setCredentials({...credentials, account: e.target.value})}
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-text-muted uppercase tracking-wider">Username</label>
                                        <div className="relative group">
                                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-primary transition-colors text-text-muted">
                                                <LayoutGrid className="w-4.5 h-4.5" />
                                            </div>
                                            <input 
                                                required
                                                className="w-full bg-[#0f1a2e] border border-border rounded-xl py-3 pl-10 pr-4 text-white focus:outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-text-muted/40"
                                                placeholder="SF_USER"
                                                value={credentials.username}
                                                onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-text-muted uppercase tracking-wider">Password</label>
                                        <div className="relative group">
                                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-primary transition-colors text-text-muted">
                                                <Key className="w-4.5 h-4.5" />
                                            </div>
                                            <input 
                                                required
                                                type="password"
                                                className="w-full bg-[#0f1a2e] border border-border rounded-xl py-3 pl-10 pr-4 text-white focus:outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-text-muted/40"
                                                placeholder="••••••••"
                                                value={credentials.password}
                                                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <button 
                                    className="w-full btn-primary py-4 text-base mt-4 flex items-center justify-center gap-2 group"
                                    disabled={loading}
                                >
                                    {loading ? (
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    ) : (
                                        <ShieldCheck className="w-5 h-5 transition-transform group-hover:scale-110" />
                                    )}
                                    {loading ? 'Analyzing Account...' : 'Connect to Snowflake'}
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleLoad} className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-text-muted uppercase tracking-wider">Session Token</label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-primary transition-colors text-text-muted">
                                            <Search className="w-4.5 h-4.5" />
                                        </div>
                                        <textarea 
                                            required
                                            rows={3}
                                            className="w-full bg-[#0f1a2e] border border-border rounded-xl py-3 pl-10 pr-4 text-white focus:outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-text-muted/40 font-mono text-sm leading-relaxed"
                                            placeholder="Paste your encrypted session ID here..."
                                            value={sessionId}
                                            onChange={(e) => setSessionId(e.target.value)}
                                        />
                                    </div>
                                    <p className="text-[10px] text-text-muted/60 mt-2 px-1">You can find your session token in the previous dashboard session details.</p>
                                </div>

                                <button 
                                    className="w-full btn-primary py-4 text-base flex items-center justify-center gap-2"
                                    disabled={loading}
                                >
                                    {loading ? (
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    ) : (
                                        <LayoutGrid className="w-5 h-5" />
                                    )}
                                    {loading ? 'Restoring Session...' : 'Load Existing Session'}
                                </button>
                            </form>
                        )}
                    </div>
                </div>

                <div className="mt-8 text-center">
                    <p className="text-xs text-text-muted leading-relaxed">
                        Read-only access. SnowAdvisor does not modify your Snowflake configuration.
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Login;
