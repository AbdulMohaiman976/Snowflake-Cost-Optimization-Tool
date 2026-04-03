import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion } from 'framer-motion';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';
import { 
  Archive, 
  AlertCircle, 
  FileCheck, 
  Flame, 
  Database,
  ArrowRight,
  TrendingDown,
  Info,
  Sparkles
} from 'lucide-react';

const StorageAnalytics = () => {
    const { session } = useAuth();
    const storageData = session?.storage || {};
    const tables = storageData.tables || [];

    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs] = useState('');

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'storage');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Failed to generate prescriptive SQL steps.');
        } finally {
            setIsGenerating(false);
        }
    };

    const storageUsage = [
        { name: 'Active', value: storageData.total_active_gb, color: '#2563eb' },
        { name: 'Waste', value: storageData.total_waste_usd * 43.4, color: '#ef4444' } // approximate GB
    ];

    const topTables = tables
        .sort((a, b) => b.active_gb - a.active_gb)
        .slice(0, 10);

    return (
        <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            className="space-y-8"
        >
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">Storage Analytics</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Optimization of data footprint, Time Travel overhead, and Failsafe identification across your databases.</p>
                </div>
                <div className="flex gap-4">
                  <div className="p-4 bg-sidebar/50 border border-border rounded-xl">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Total Active (GB)</p>
                    <p className="text-xl font-black text-white font-mono">{storageData.total_active_gb?.toFixed(2)}</p>
                  </div>
                  <div className="p-4 bg-sidebar/50 border border-border rounded-xl">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Bloated Tables</p>
                    <p className="text-xl font-black text-danger font-mono">{storageData.bloated_count}</p>
                  </div>
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
                            <p className="text-[10px] text-text-muted font-black uppercase tracking-widest">Real-time Prescriptive Intelligence</p>
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
                    <div className="w-full mt-4 p-4 bg-background/50 border border-primary/20 rounded-xl relative overflow-hidden group">
                       <div className="absolute top-0 right-0 p-2 text-[10px] text-primary/40 font-bold uppercase tracking-widest border-l border-b border-primary/20 bg-primary/5">GROQ SYNTHESIS</div>
                       <pre className="text-sm font-mono text-text-accent leading-relaxed whitespace-pre-wrap overflow-x-auto">{runtimeRecs}</pre>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-5 gap-6">
                <div className="col-span-3 glass-card p-6">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6">Largest Tables by Footprint</h3>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={topTables} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <XAxis dataKey="table" hide />
                                <YAxis 
                                    fontSize={10} 
                                    stroke="#4b5563" 
                                    axisLine={false} 
                                    tickLine={false}
                                    tickFormatter={(v) => `${v}GB`}
                                />
                                <Tooltip 
                                    contentStyle={{ 
                                        backgroundColor: '#0d1829', 
                                        border: '1px solid #1a2e4a',
                                        borderRadius: '8px',
                                        fontSize: '11px',
                                        color: '#fff'
                                    }}
                                />
                                <Bar dataKey="active_gb" fill="#2563eb" radius={[6, 6, 0, 0]} barSize={24}>
                                    {topTables.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.bloat_pct > 100 ? '#ef4444' : '#2563eb'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="col-span-2 space-y-6">
                    <div className="glass-card p-6 border-l-[6px] border-danger bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-[140px]">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Flame className="w-4 h-4 text-danger" />
                            <h4 className="text-xs font-bold text-white uppercase tracking-widest">Monthly Cost Loss</h4>
                          </div>
                          <p className="text-[10px] text-text-muted/80 leading-relaxed font-medium">Estimated monthly loss due to excessive data retention and time travel overhead.</p>
                        </div>
                        <h2 className="text-4xl font-extrabold text-danger font-mono tracking-tighter">${storageData.total_waste_usd?.toFixed(2)}</h2>
                    </div>

                    <div className="glass-card p-6 border-l-[6px] border-success bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-[140px]">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <TrendingDown className="w-4 h-4 text-success" />
                            <h4 className="text-xs font-bold text-white uppercase tracking-widest">Potential Capacity Savings</h4>
                          </div>
                          <p className="text-[10px] text-text-muted/80 leading-relaxed font-medium">Reduce your storage footprint by optimizing Time Travel for temporary dev tables.</p>
                        </div>
                        <h2 className="text-4xl font-extrabold text-success font-mono tracking-tighter">~4.5 TB</h2>
                    </div>
                </div>
            </div>

            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-border bg-sidebar/30 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white uppercase tracking-widest">Storage Footprint Registry</h3>
                  <div className="flex items-center gap-2">
                    <span className="p-1 px-3 rounded-lg bg-white/5 border border-white/10 text-[10px] font-extrabold text-text-muted uppercase">Top {tables.length} Objects</span>
                    <button className="p-1 px-3 rounded-lg hover:bg-white/5 border border-border text-[10px] font-extrabold text-text-muted uppercase flex items-center gap-1.5"><Archive className="w-3.5 h-3.5" /> Export Inventory</button>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-sidebar/50 text-[10px] font-bold text-text-muted uppercase tracking-widest border-b border-border">
                                <th className="px-6 py-4">Database Object</th>
                                <th className="px-6 py-4 text-right">Active (GB)</th>
                                <th className="px-6 py-4 text-right">Time Travel</th>
                                <th className="px-6 py-4 text-right">Failsafe</th>
                                <th className="px-6 py-4">Overhead %</th>
                                <th className="px-6 py-4 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                            {tables.map((table, idx) => (
                                <tr key={idx} className="group hover:bg-white/[0.02] transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="text-sm font-bold text-white group-hover:text-primary-light flex items-center gap-2">
                                                {table.table}
                                                {table.is_system && <span className="text-[8px] px-1.5 py-0.5 bg-sidebar rounded border border-border text-text-muted/40 uppercase font-black tracking-widest">SYSTEM</span>}
                                            </span>
                                            <span className="text-[10px] text-text-muted font-mono">{table.database}.{table.schema}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right font-mono text-[13px] text-white font-bold">{table.active_gb?.toFixed(2)}</td>
                                    <td className="px-6 py-4 text-right font-mono text-[11px] text-text-muted">{table.tt_gb?.toFixed(2)} GB</td>
                                    <td className="px-6 py-4 text-right font-mono text-[11px] text-text-muted">{table.fs_gb?.toFixed(2)} GB</td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="flex-1 h-1.5 bg-sidebar-item rounded-full overflow-hidden border border-border">
                                                <div className={`h-full bg-${table.bloat_pct > 100 ? 'danger' : table.bloat_pct > 50 ? 'warning' : 'success'}`} style={{ width: `${Math.min(table.bloat_pct, 100)}%` }}></div>
                                            </div>
                                            <span className={`text-[10px] font-bold min-w-[30px] ${table.bloat_pct > 100 ? 'text-danger' : 'text-text-muted'}`}>{table.bloat_pct?.toFixed(0)}%</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className={`px-2 py-1 rounded inline-flex items-center gap-1.5 border text-[10px] font-bold uppercase transition-colors ${table.bloat_pct > 100 ? 'bg-danger/10 border-danger/20 text-danger' : 'bg-success/10 border-success/20 text-success'}`}>
                                          {table.bloat_pct > 100 ? (
                                            <>
                                              <AlertCircle className="w-3.5 h-3.5" /> Bloated
                                            </>
                                          ) : (
                                            <>
                                              <FileCheck className="w-3.5 h-3.5" /> Healthy
                                            </>
                                          )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </motion.div>
    );
};

export default StorageAnalytics;
