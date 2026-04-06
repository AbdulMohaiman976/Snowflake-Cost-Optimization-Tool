import React, { useState } from 'react';
import { Snowflake, ShieldCheck, Database, Key, LayoutGrid } from 'lucide-react';
import { connectToSnowflake } from '../api/api';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';

const Login = () => {
    const [credentials, setCredentials] = useState({ account: '', username: '', password: '', warehouse: 'COMPUTE_WH', role: 'ACCOUNTADMIN' });
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

    return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-background relative overflow-hidden">
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
                        <Snowflake className="w-10 h-10 text-[#2C7DA0]" strokeWidth={1.5} />
                    </div>
                    <h1 className="text-4xl font-extrabold tracking-tight mb-3">
                        <span className="text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.1)]">Snow</span>
                        <span className="text-[#2C7DA0]">Advisor</span>
                    </h1>
                    <p className="text-white text-lg drop-shadow-[0_1px_2px_rgba(0,0,0,0.1)]">Premium Snowflake Cost Intelligence Dashboard</p>
                </div>

                <div className="glass-card overflow-hidden">
                    <div className="bg-white/10 border-b border-white/20 p-6">
                        <h2 className="text-lg font-bold text-[#2C7DA0] flex items-center gap-2">
                             <ShieldCheck className="w-5 h-5 text-[#2C7DA0]" />
                             Snowflake Authentication
                        </h2>
                        <p className="text-xs text-white/70 mt-1">Connect your account to access cost optimization insights.</p>
                    </div>

                    <div className="p-8">
                        {error && (
                            <div className="mb-6 p-4 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm flex items-start gap-3">
                                <div className="p-1 rounded-md bg-danger/10">⚠️</div>
                                <p className="leading-relaxed">{typeof error === 'string' ? error : JSON.stringify(error)}</p>
                            </div>
                        )}

                        <form onSubmit={handleConnect} className="space-y-5">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-text-muted uppercase tracking-wider">Account Identifier</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-primary transition-colors text-text-muted">
                                        <Database className="w-4.5 h-4.5" />
                                    </div>
                                    <input 
                                        required
                                        className="w-full bg-white border border-white/30 rounded-xl py-3 pl-10 pr-4 text-[#2C7DA0] focus:outline-none focus:border-white/50 focus:ring-4 focus:ring-white/10 transition-all placeholder:text-[#2C7DA0]/40"
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
                                            className="w-full bg-white border border-white/30 rounded-xl py-3 pl-10 pr-4 text-[#2C7DA0] focus:outline-none focus:border-white/50 focus:ring-4 focus:ring-white/10 transition-all placeholder:text-[#2C7DA0]/40"
                                            placeholder="SF_USER"
                                            value={credentials.username}
                                            onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-white/70 uppercase tracking-wider">Password</label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-white transition-colors text-white/50">
                                            <Key className="w-4.5 h-4.5" />
                                        </div>
                                        <input 
                                            required
                                            type="password"
                                            className="w-full bg-white border border-white/30 rounded-xl py-3 pl-10 pr-4 text-[#2C7DA0] focus:outline-none focus:border-white/50 focus:ring-4 focus:ring-white/10 transition-all placeholder:text-[#2C7DA0]/40"
                                            placeholder="••••••••"
                                            value={credentials.password}
                                            onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                                        />
                                    </div>
                                </div>
                            </div>

                            <button 
                                className="w-full bg-[#2C7DA0] hover:bg-[#236480] text-white font-bold py-4 rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 group"
                                disabled={loading}
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    <ShieldCheck className="w-5 h-5 transition-transform group-hover:scale-110" />
                                )}
                                {loading ? 'Analyzing Snowflake Account...' : 'Sign In and Sync Dashboard'}
                            </button>
                        </form>
                    </div>
                </div>

                <div className="mt-8 text-center">
                    <p className="text-xs text-text-muted leading-relaxed">
                        Read-only access. SnowAdvisor does not modify your Snowflake configuration.
                        <br />
                        Data is securely isolated in your private MongoDB cloud.
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Login;
