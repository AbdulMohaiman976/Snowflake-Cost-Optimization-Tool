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
        <div
            className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden"
            style={{
                background:
                    'linear-gradient(135deg, #a9ddf5 0%, #d9f1ff 45%, #f2fbff 100%)',
            }}
        >
            {/* Geometric background shapes */}
            <div
                className="absolute inset-0"
                style={{
                    background:
                        'linear-gradient(135deg, rgba(255,255,255,0.55) 0%, rgba(255,255,255,0.15) 40%, rgba(255,255,255,0) 100%)',
                    clipPath: 'polygon(0 0, 70% 0, 40% 100%, 0 100%)',
                }}
            ></div>
            <div
                className="absolute inset-0"
                style={{
                    background:
                        'linear-gradient(315deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0) 60%)',
                    clipPath: 'polygon(60% 0, 100% 0, 100% 100%, 25% 100%)',
                }}
            ></div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-lg relative z-10"
            >
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white border border-black/10 mb-6">
                        <Snowflake className="w-10 h-10 text-[#2C7DA0]" strokeWidth={1.5} />
                    </div>
                    <h1 className="text-4xl font-extrabold tracking-tight mb-3">
                        <span className="text-black">Snow</span>
                        <span className="text-[#2C7DA0]">Advisor</span>
                    </h1>
                    <p className="text-black text-lg">Premium Snowflake Cost Intelligence Dashboard</p>
                </div>

                <div className="overflow-hidden rounded-2xl border border-black/10 bg-white shadow-[0_20px_60px_rgba(0,0,0,0.08)]">
                    <div className="bg-white border-b border-black/10 p-6">
                        <h2 className="text-lg font-bold text-[#2C7DA0] flex items-center gap-2">
                             <ShieldCheck className="w-5 h-5 text-[#2C7DA0]" />
                             Snowflake Authentication
                        </h2>
                        <p className="text-xs text-black mt-1">Connect your account to access cost optimization insights.</p>
                    </div>

                    <div className="p-8">
                        {error && (
                            <div className="mb-6 p-4 rounded-lg bg-white border border-black/20 text-black text-sm flex items-start gap-3">
                                <div className="p-1 rounded-md bg-white">??</div>
                                <p className="leading-relaxed">{typeof error === 'string' ? error : JSON.stringify(error)}</p>
                            </div>
                        )}

                        <form onSubmit={handleConnect} className="space-y-5">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-black uppercase tracking-wider">Account Identifier</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-[#2C7DA0] transition-colors text-black">
                                        <Database className="w-4.5 h-4.5" />
                                    </div>
                                    <input
                                        required
                                        className="w-full bg-white border border-black/15 rounded-xl py-3 pl-10 pr-4 text-black focus:outline-none focus:border-[#2C7DA0] focus:ring-4 focus:ring-[#2C7DA0]/15 transition-all placeholder:text-black/40"
                                        placeholder="abc12345.us-east-1"
                                        value={credentials.account}
                                        onChange={(e) => setCredentials({...credentials, account: e.target.value})}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-black uppercase tracking-wider">Username</label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-[#2C7DA0] transition-colors text-black">
                                            <LayoutGrid className="w-4.5 h-4.5" />
                                        </div>
                                        <input
                                            required
                                            className="w-full bg-white border border-black/15 rounded-xl py-3 pl-10 pr-4 text-black focus:outline-none focus:border-[#2C7DA0] focus:ring-4 focus:ring-[#2C7DA0]/15 transition-all placeholder:text-black/40"
                                            placeholder="SF_USER"
                                            value={credentials.username}
                                            onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-black uppercase tracking-wider">Password</label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none group-focus-within:text-[#2C7DA0] transition-colors text-black">
                                            <Key className="w-4.5 h-4.5" />
                                        </div>
                                        <input
                                            required
                                            type="password"
                                            className="w-full bg-white border border-black/15 rounded-xl py-3 pl-10 pr-4 text-black focus:outline-none focus:border-[#2C7DA0] focus:ring-4 focus:ring-[#2C7DA0]/15 transition-all placeholder:text-black/40"
                                            placeholder="????????"
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
                    <p className="text-xs text-black leading-relaxed">
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
