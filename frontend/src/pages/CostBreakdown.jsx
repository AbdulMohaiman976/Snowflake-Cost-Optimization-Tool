import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion } from 'framer-motion';
import { 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  ResponsiveContainer, 
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid
} from 'recharts';
import { 
  DollarSign, 
  Users, 
  BarChart3, 
  TrendingUp, 
  ArrowUpRight,
  User,
  Layers,
  ArrowRight,
  Sparkles
} from 'lucide-react';

const CostBreakdown = () => {
    const { session } = useAuth();
    const cost = session?.cost || {};
    const byUser = cost.by_user || [];
    const whAnalysis = cost.wh_analysis || [];

    const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs] = useState('');

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'cost');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Could not generate cost remediation steps.');
        } finally {
            setIsGenerating(false);
        }
    };

    const pieData = whAnalysis.slice(0, 5).map(w => ({
        name: w.warehouse,
        value: w.total_credits
    }));

    return (
        <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-8"
        >
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">Cost Breakdown</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Granular analysis of credit consumption by compute cluster, user workload, and data ownership.</p>
                </div>
                <div className="flex gap-4 p-4 bg-sidebar/50 border border-border rounded-xl">
                  <div className="pr-6 border-r border-border/50">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Total Credit Spend</p>
                    <p className="text-xl font-black text-white font-mono">{cost.total_credits?.toFixed(2)}</p>
                  </div>
                  <div className="pl-2">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Market Price (USD)</p>
                    <p className="text-xl font-black text-success font-mono">${cost.total_cost_usd?.toLocaleString()}</p>
                  </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
                <div className="glass-card p-6">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-8">Credits by Warehouse (Top 5)</h3>
                    <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip 
                                    contentStyle={{ 
                                        backgroundColor: '#0d1829', 
                                        border: '1px solid #1a2e4a',
                                        borderRadius: '8px',
                                        fontSize: '11px',
                                        color: '#fff'
                                    }}
                                />
                                <Legend 
                                    verticalAlign="middle" 
                                    align="right" 
                                    layout="vertical"
                                    formatter={(value) => <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{value}</span>}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="glass-card p-6">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-8">User Cost Attribution</h3>
                    <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={byUser.slice(0, 10)} layout="vertical">
                                <XAxis type="number" hide />
                                <YAxis 
                                    dataKey="user" 
                                    type="category" 
                                    width={100} 
                                    fontSize={10} 
                                    stroke="#4b5563"
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <Bar dataKey="queries" fill="#2563eb" radius={[0, 4, 4, 0]} barSize={12} />
                                <Tooltip 
                                    contentStyle={{ 
                                        backgroundColor: '#0d1829', 
                                        border: '1px solid #1a2e4a',
                                        borderRadius: '8px',
                                        fontSize: '11px'
                                    }}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-border flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white uppercase tracking-widest">User Workload Profiles</h3>
                  <div className="flex gap-2 text-[10px] font-bold text-text-muted uppercase tracking-widest">
                     <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-primary"></div> High Spend</span>
                     <span className="flex items-center gap-1.5 pl-4"><div className="w-2 h-2 rounded-full bg-success"></div> Optimized</span>
                  </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-sidebar/50 text-[10px] font-bold text-text-muted uppercase tracking-widest border-b border-border">
                                <th className="px-6 py-4">User & Role</th>
                                <th className="px-6 py-4">Profile</th>
                                <th className="px-6 py-4 text-right">Queries</th>
                                <th className="px-6 py-4 text-right">Avg Duration</th>
                                <th className="px-6 py-4 text-right">Resource Share</th>
                                <th className="px-6 py-4">Insight</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                            {byUser.map((user, idx) => (
                                <tr key={idx} className="group hover:bg-white/[0.02] transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-sidebar border border-border rounded-lg text-text-muted group-hover:text-primary transition-colors">
                                                {user.is_system ? <Layers className="w-4 h-4" /> : <User className="w-4 h-4" />}
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-sm font-bold text-white leading-tight">{user.user}</span>
                                                <span className="text-[10px] text-text-muted font-mono tracking-tighter uppercase">{user.role}</span>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className={`px-2 py-1 rounded text-[10px] font-bold inline-block border ${user.is_system ? 'border-primary/20 text-primary-light bg-primary/10' : 'border-border text-text-muted bg-sidebar'}`}>
                                            {user.profile}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right font-mono text-xs font-bold text-white">{user.queries?.toLocaleString()}</td>
                                    <td className="px-6 py-4 text-right font-mono text-xs text-text-accent">{user.avg_exec_sec?.toFixed(2)}s</td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex flex-col items-end gap-1.5">
                                            <div className="w-16 h-1 bg-border rounded-full overflow-hidden">
                                                <div className="h-full bg-primary" style={{ width: `${user.query_share}%` }}></div>
                                            </div>
                                            <span className="text-[10px] font-bold text-text-muted">{user.query_share}% Share</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <p className="text-[10px] text-text-muted max-w-xs">{user.note}</p>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="glass-card p-6 bg-primary/5 border border-dashed border-primary/30 flex flex-col items-start gap-4">
                <div className="flex justify-between items-center w-full">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/20 rounded-lg">
                            <Sparkles className="w-5 h-5 text-primary-light" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white uppercase tracking-widest leading-none mb-1">AI Recommendation</h3>
                            <p className="text-[10px] text-text-muted font-black uppercase tracking-widest">Real-time Prescriptive Intelligence — Cost Breakdown Rules</p>
                        </div>
                    </div>
                    <button 
                        onClick={handleExecuteAdvice}
                        disabled={isGenerating}
                        className={`px-6 py-2 bg-primary text-white text-xs font-bold rounded-lg transition-all ${isGenerating ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary-dark'}`}
                    >
                        {isGenerating ? 'Generating...' : 'Execute AI Analysis'}
                    </button>
                </div>
                {runtimeRecs && (
                    <div className="w-full mt-4 p-4 bg-background/50 border border-primary/20 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 text-[10px] text-primary/40 font-bold uppercase tracking-widest border-l border-b border-primary/20 bg-primary/5">GROQ SYNTHESIS</div>
                        <pre className="text-sm font-mono text-text-accent leading-relaxed whitespace-pre-wrap overflow-x-auto pt-4">{runtimeRecs}</pre>
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default CostBreakdown;
