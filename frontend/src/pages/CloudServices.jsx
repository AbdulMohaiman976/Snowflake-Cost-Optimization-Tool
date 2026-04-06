import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion } from 'framer-motion';
import { 
  Cloud, 
  Search, 
  Layers, 
  BarChart, 
  Database,
  TrendingDown,
  Info,
  ChevronRight,
  Zap,
  ArrowUpRight,
  Sparkles
} from 'lucide-react';

const CloudServices = () => {
    const { session } = useAuth();
    const cloud = session?.cloud_services || {};
    const warehouses = cloud.warehouses || [];
    const totalCloud = cloud.total_cloud_credits || 0;

    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs] = useState('');

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'cloud_services');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Failed to generate prescriptive SQL steps.');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-8"
        >
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">Cloud Services</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Analysis of the Snowflake internal services layer, including metadata operations and query compilation across all workloads.</p>
                </div>
                <div className="flex gap-4 p-4 bg-sidebar/50 border border-border rounded-xl backdrop-blur-xl">
                  <div className="pr-6 border-r border-border/50">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Total Cloud Credits</p>
                    <p className="text-xl font-black text-white font-mono">{totalCloud?.toFixed(4)}</p>
                  </div>
                  <div className="pl-2">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Market Price (USD)</p>
                    <p className="text-xl font-black text-primary-light font-mono">${(totalCloud * 3).toLocaleString()}</p>
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

            <div className="grid grid-cols-4 gap-6 mb-8">
                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-primary/10 border border-primary/20 rounded-lg w-fit mb-4">
                            <Cloud className="w-5 h-5 text-primary-light" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1">Metadata Overhead</p>
                        <h4 className="text-2xl font-extrabold text-white">
                            {warehouses.length > 0 ? (warehouses.reduce((acc, w) => acc + w.cloud_pct, 0) / warehouses.length).toFixed(1) : 0}%
                        </h4>
                    </div>
                    <div className="text-[10px] text-text-muted font-bold flex items-center gap-1.5 uppercase tracking-widest">
                       <TrendingDown className="w-3.5 h-3.5 opacity-20" /> Performance Ratio
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44 border-l-4 border-warning">
                    <div>
                        <div className="p-2 bg-warning/10 border border-warning/20 rounded-lg w-fit mb-4">
                            <Zap className="w-5 h-5 text-warning" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1 leading-none">Compute vs Cloud</p>
                        <h4 className="text-2xl font-extrabold text-white">{warehouses.length} clusters</h4>
                    </div>
                    <div className="text-[10px] text-text-muted font-bold flex items-center gap-1.5 uppercase tracking-widest leading-none">
                       <ArrowUpRight className="w-3 h-3 opacity-20" /> Active Infrastructure
                    </div>
                </div>

                <div className="col-span-2 p-6 glass-card border border-primary/20 bg-primary/5 relative overflow-hidden group hover:border-primary/40 transition-colors cursor-pointer">
                  <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><Zap className="w-24 h-24 text-primary-light" /></div>
                    <div>
                        <p className="text-[10px] text-primary-light font-black uppercase tracking-[0.2em] mb-4 leading-none">Cloud Strategy Recommendation</p>
                        <h4 className="text-lg font-bold text-white mb-2 max-w-sm leading-tight font-mono">
                            {warehouses.length > 0 
                                ? `Optimize compilation overhead for ${warehouses[0].warehouse} by batching workloads.`
                                : "No active cloud service hotspots detected."}
                        </h4>
                    </div>
                    <div className="mt-4 flex items-center gap-3">
                        <button className="py-1.5 px-4 bg-primary text-white text-[10px] font-black uppercase rounded-lg transition-all shadow-md">Run Deep Audit</button>
                    </div>
                </div>
            </div>

            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-border bg-sidebar/30 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white uppercase tracking-widest">Warehouse Level Cloud Performance</h3>
                  <div className="flex gap-2">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
                        <input className="bg-sidebar-item border border-border rounded-lg py-1.5 pl-8 pr-3 text-[11px] text-white focus:outline-none focus:border-primary/50 transition-all w-[240px]" placeholder="Search warehouse..." />
                    </div>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-sidebar/50 text-[10px] font-bold text-text-muted uppercase tracking-widest border-b border-border">
                                <th className="px-6 py-4 font-bold">Warehouse Cluster</th>
                                <th className="px-6 py-4 text-right font-bold">Cloud Credits</th>
                                <th className="px-6 py-4 text-right font-bold">Compute Credits</th>
                                <th className="px-6 py-4 text-right font-bold">Total Spend</th>
                                <th className="px-6 py-4 font-bold">Cloud Share</th>
                                <th className="px-6 py-4 text-right">Analysis</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                            {warehouses.map((wh, idx) => (
                                <tr key={idx} className="group hover:bg-white/[0.02] transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-sidebar border border-border rounded-lg text-text-muted group-hover:text-primary transition-colors">
                                                <Database className="w-4 h-4" />
                                            </div>
                                            <span className="text-xs font-bold text-white group-hover:text-primary transition-colors">{wh.warehouse}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right font-mono text-[11px] text-text-accent font-bold group-hover:scale-105 transition-transform origin-right">{wh.cloud_credits?.toFixed(4)}</td>
                                    <td className="px-6 py-4 text-right font-mono text-[11px] text-text-muted">{wh.compute_credits?.toFixed(4)}</td>
                                    <td className="px-6 py-4 text-right font-mono text-[11px] text-white font-bold">{wh.total_credits?.toFixed(4)}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-3">
                                            <div className="flex-1 h-1 bg-border rounded-full overflow-hidden w-20">
                                                <div className={`h-full bg-primary`} style={{ width: `${Math.min(wh.cloud_pct, 100)}%` }}></div>
                                            </div>
                                            <span className={`text-[10px] font-bold ${wh.cloud_pct > 10 ? 'text-primary-light' : 'text-text-muted'}`}>{wh.cloud_pct}%</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button className="group flex items-center justify-end gap-1.5 p-1 px-3 text-[10px] font-black uppercase text-primary transition-colors hover:text-white">Profile <ArrowUpRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" /></button>
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

export default CloudServices;
