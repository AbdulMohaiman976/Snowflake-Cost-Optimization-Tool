import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion } from 'framer-motion';
import { 
  Plus, 
  Search, 
  Trash2, 
  AlertTriangle, 
  Layers, 
  Database,
  ArrowRight,
  TrendingDown,
  Info,
  Sparkles
} from 'lucide-react';

const UnusedObjects = () => {
    const { session } = useAuth();
    const unused = session?.unused_objects || {};
    const tables = unused.tables || [];

    const totalSavings = unused.potential_savings_usd || 0;
    const totalSize = unused.total_size_gb || 0;

    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs] = useState('');

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'unused_objects');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Failed to generate prescriptive SQL steps.');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-8"
        >
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">Unused Objects</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Cleanup recommendations for stale tables, temporary objects, and unused schemas that haven't been accessed in 30+ days.</p>
                </div>
                <div className="flex gap-4 p-4 bg-sidebar/50 border border-border rounded-xl">
                  <div className="pr-6 border-r border-border/50">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Potential Savings</p>
                    <p className="text-xl font-black text-success font-mono">${totalSavings?.toFixed(2)}/mo</p>
                  </div>
                  <div className="pl-2">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Recoverable Size</p>
                    <p className="text-xl font-black text-white font-mono">{totalSize?.toFixed(2)} GB</p>
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

            <div className="grid grid-cols-4 gap-6">
                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-primary/10 border border-primary/20 rounded-lg w-fit mb-4">
                            <Layers className="w-5 h-5 text-primary-light" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1 leading-none">Stale Tables</p>
                        <h4 className="text-2xl font-extrabold text-white">{tables.length}</h4>
                    </div>
                    <div className="text-[10px] text-text-muted font-bold flex items-center gap-1.5 uppercase tracking-widest">
                       <div className="w-1.5 h-1.5 bg-danger rounded-full"></div> Requires cleanup
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44 border-l-4 border-primary">
                    <div>
                        <div className="p-2 bg-primary/10 border border-primary/20 rounded-lg w-fit mb-4">
                            <Database className="w-5 h-5 text-primary-light" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1 leading-none">Largest Stale</p>
                        <h4 className="text-2xl font-extrabold text-white">{tables.length > 0 ? tables[0].size_gb : 0} GB</h4>
                    </div>
                    <div className="text-[10px] text-text-muted font-bold flex items-center gap-1.5 uppercase tracking-widest">
                       <div className="w-1.5 h-1.5 bg-primary rounded-full"></div> Top space consumer
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-warning/10 border border-warning/20 rounded-lg w-fit mb-4">
                            <TrendingDown className="w-5 h-5 text-warning" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1 leading-none">Avg Stale Age</p>
                        <h4 className="text-2xl font-extrabold text-white">
                            {tables.length > 0 
                                ? Math.round(tables.reduce((acc, t) => acc + (new Date() - new Date(t.last_altered)) / (1000 * 60 * 60 * 24), 0) / tables.length)
                                : 0} Days
                        </h4>
                    </div>
                    <div className="text-[10px] text-text-muted font-bold flex items-center gap-1.5 uppercase tracking-widest">
                       <div className="w-1.5 h-1.5 bg-warning rounded-full"></div> {tables.length > 0 ? 'Actionable objects' : 'Optimal state'}
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44 backdrop-blur-3xl overflow-hidden relative group">
                  <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-15 transition-opacity"><Layers className="w-20 h-20 text-white" /></div>
                    <div>
                        <p className="text-[10px] text-primary font-black uppercase tracking-[0.2em] mb-4 leading-none">AI Priority</p>
                        <h4 className="text-xl font-bold text-white line-clamp-1">{tables.length > 10 ? 'High Cleanup' : 'Regular Audit'}</h4>
                    </div>
                    <div className="w-full h-8 flex items-center justify-center border border-primary/20 rounded-lg text-[10px] font-bold text-primary-light uppercase tracking-widest">
                        {tables.length > 0 ? 'Awaiting Action' : 'All Clear'}
                    </div>
                </div>
            </div>

            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-border bg-sidebar/30 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white uppercase tracking-widest">Candidate Tables for Deletion</h3>
                  <div className="flex gap-2">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
                        <input className="bg-sidebar-item border border-border rounded-lg py-1.5 pl-8 pr-3 text-[11px] text-white focus:outline-none focus:border-primary/50 transition-all w-[240px]" placeholder="Search stale schemas..." />
                    </div>
                    <button className="p-1 px-3 rounded-lg hover:bg-white/5 border border-border text-text-muted font-black text-[10px] uppercase">Filter Age</button>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-sidebar/50 text-[10px] font-bold text-text-muted uppercase tracking-widest border-b border-border">
                                <th className="px-6 py-4">Full Table Name</th>
                                <th className="px-6 py-4">Table Type</th>
                                <th className="px-6 py-4 text-right">Row Count</th>
                                <th className="px-6 py-4 text-right">Size (GB)</th>
                                <th className="px-6 py-4">Inactive Since</th>
                                <th className="px-6 py-4 text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                            {tables.map((table, idx) => (
                                <tr key={idx} className="group hover:bg-white/[0.02] transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-sidebar border border-border rounded lg text-text-muted group-hover:text-danger-light group-hover:bg-danger/10 group-hover:border-danger/30 transition-all">
                                                <Database className="w-3.5 h-3.5" />
                                            </div>
                                            <span className="text-xs font-bold text-white group-hover:text-danger-light transition-colors truncate max-w-sm">{table.name}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 font-mono text-[10px] text-text-muted uppercase">{table.type}</td>
                                    <td className="px-6 py-4 text-right font-mono text-[11px] text-text-accent">{table.rows?.toLocaleString()}</td>
                                    <td className="px-6 py-4 text-right font-mono text-[11px] text-white font-bold">{table.size_gb?.toFixed(2)}</td>
                                    <td className="px-6 py-4 font-mono text-[10px] text-text-muted">
                                        {new Date(table.last_altered).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <button className="p-1 px-3 rounded-lg text-[10px] font-black uppercase text-danger hover:bg-danger/10 transition-colors border border-transparent hover:border-danger/40">Drop</button>
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

export default UnusedObjects;
