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
  Calendar,
  History,
  TrendingUp,
  ArrowDownCircle,
  Zap,
  ArrowUpRight,
  Sparkles
} from 'lucide-react';

const SavingsHistory = () => {
    const { session } = useAuth();
    const savings = session?.savings || {};
    const items = savings.recommendations || [];

    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs] = useState('');

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'savings');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Could not generate savings remediation steps.');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <motion.div 
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.02 }}
            className="space-y-8"
        >
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-text mb-2">Savings & History</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Aggregated cost-saving opportunities and historical analysis of optimization runs over time.</p>
                </div>
                <div className="flex gap-4 p-4 bg-black/30 border border-border rounded-xl">
                  <div className="pr-6 border-r border-border/50 text-right">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Aggregated Savings</p>
                    <p className="text-xl font-black text-text font-mono">${(savings.total_usd || 0).toLocaleString()}/mo</p>
                  </div>
                  <div className="pl-2 text-right">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Last Analyzed</p>
                    <p className="text-sm font-black text-primary flex items-center justify-end gap-1.5 mt-1.5"><Calendar className="w-4 h-4" /> Today</p>
                  </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
                <div className="glass-card p-8 flex flex-col justify-between border-l-4 border-success overflow-hidden relative group">
                    <div className="absolute top-0 right-0 p-10 opacity-5 group-hover:opacity-10 transition-opacity"><ArrowDownCircle className="w-32 h-32 text-success" /></div>
                    <div>
                        <h3 className="text-sm font-bold text-text uppercase tracking-widest mb-2">Quick Optimization Action</h3>
                        <p className="text-xs text-text-muted/80 leading-relaxed font-medium mb-6">Implementing all current HIGH-SEVERITY recommendations will reduce monthly spend by approximately <span className="text-success font-black">$4,230</span>.</p>
                        <div className="flex gap-4">
                            <button className="flex-1 py-3 bg-success hover:bg-success-dark text-text text-[10px] font-black uppercase rounded-xl transition-all shadow-lg shadow-success/20">Apply All Best Practices</button>
                            <button className="flex-1 py-3 bg-black/5 hover:bg-black/10 border border-black/10 text-text text-[10px] font-black uppercase rounded-xl transition-all">Review Pipeline</button>
                        </div>
                    </div>
                </div>

                <div className="glass-card p-8 flex flex-col justify-between border-l-4 border-primary">
                    <div>
                        <h3 className="text-sm font-bold text-text uppercase tracking-widest mb-6">Session Execution History</h3>
                        <div className="space-y-4">
                            {[
                                { date: '2026-04-03', score: 85, cost: 1240 },
                                { date: '2026-03-30', score: 82, cost: 1350 },
                                { date: '2026-03-25', score: 79, cost: 1410 }
                            ].map((run, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-black/30 border border-border rounded-xl group hover:border-primary/50 transition-colors cursor-pointer">
                                    <div className="flex items-center gap-4">
                                        <div className="p-2 bg-primary/10 border border-primary/20 rounded-lg"><History className="w-3.5 h-3.5 text-primary" /></div>
                                        <div className="flex flex-col">
                                            <span className="text-xs font-bold text-text">{run.date} Check</span>
                                            <span className="text-[9px] text-text-muted font-bold uppercase tracking-widest">Health Score: {run.score}</span>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className="text-xs font-bold text-text-muted font-mono leading-none">${run.cost} Total Spend</span>
                                        <div className="flex items-center justify-end gap-1 mt-1 text-success text-[10px] font-bold"><TrendingDown className="w-3 h-3" /> -2.4%</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="space-y-6">
                <div className="flex items-center justify-between px-2">
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest">Master Recommendations List</h3>
                    <div className="flex items-center gap-4 text-[10px] font-bold text-text-muted/60 uppercase tracking-widest">
                        <span className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 bg-danger rounded-full"></div> HIGH</span>
                        <span className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 bg-warning rounded-full"></div> MEDIUM</span>
                        <span className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 bg-primary rounded-full"></div> LOW</span>
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {items.map((rec, idx) => (
                        <div key={idx} className={`p-6 glass-card border-l-[4px] bg-gradient-to-br from-sidebar/50 to-background flex flex-col gap-6 group hover:border-black/20 transition-all ${rec.severity === 'HIGH' ? 'border-danger' : rec.severity === 'MEDIUM' ? 'border-warning' : 'border-primary'}`}>
                            <div className="flex items-start justify-between">
                                <div className="flex gap-4">
                                    <div className={`p-3 rounded-2xl border ${rec.severity === 'HIGH' ? 'bg-danger/10 border-danger/20 text-danger' : rec.severity === 'MEDIUM' ? 'bg-warning/10 border-warning/20 text-warning' : 'bg-primary/10 border-primary/20 text-primary'}`}>
                                        <Zap className="w-6 h-6" strokeWidth={1} />
                                    </div>
                                    <div className="flex flex-col gap-1">
                                      <h4 className="text-base font-bold text-text tracking-tight">{rec.title}</h4>
                                      <p className="text-xs text-text-muted max-w-2xl leading-relaxed">{rec.detail}</p>
                                    </div>
                                </div>
                                <div className="flex flex-col items-end gap-3">
                                   <div className={`p-1 px-3 rounded-md text-[10px] font-black uppercase text-text ${rec.severity === 'HIGH' ? 'bg-danger' : rec.severity === 'MEDIUM' ? 'bg-warning text-black' : 'bg-primary'}`}>
                                       {rec.severity} SEVERITY
                                   </div>
                                    <span className="text-[10px] text-text-muted font-bold flex items-center gap-1.5 uppercase tracking-widest cursor-pointer hover:text-text transition-colors underline underline-offset-4">Read full analysis <ArrowUpRight className="w-3 h-3" /></span>
                                </div>
                            </div>
                            
                            {rec.fix_sql && (
                                <div className="bg-[#C6F2FF] rounded-xl border border-border/40 p-5 font-mono text-xs text-text-accent leading-relaxed relative flex flex-col group/code">
                                    <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/5 opacity-40 group-hover/code:opacity-100 transition-opacity">
                                       <span className="text-[9px] font-black uppercase tracking-[0.2em] text-primary">Proposed Resolution SQL</span>
                                       <button className="flex items-center gap-1.5 p-1 px-2 border border-primary/20 bg-primary/20 text-[9px] font-bold text-primary uppercase rounded transition-colors hover:bg-primary hover:text-text">Copy Command</button>
                                    </div>
                                    <code className="whitespace-pre-wrap">{rec.fix_sql}</code>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            <div className="glass-card p-6 bg-primary/5 border border-dashed border-primary/30 flex flex-col items-start gap-4">
                <div className="flex justify-between items-center w-full">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/20 rounded-lg">
                            <Sparkles className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-text uppercase tracking-widest leading-none mb-1">AI Recommendation</h3>
                            <p className="text-[10px] text-text-muted font-black uppercase tracking-widest">Real-time Prescriptive Intelligence — Savings &amp; Optimization Rules</p>
                        </div>
                    </div>
                    <button 
                        onClick={handleExecuteAdvice}
                        disabled={isGenerating}
                        className={`px-6 py-2 bg-primary text-text text-xs font-bold rounded-lg transition-all ${isGenerating ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary-dark'}`}
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

export default SavingsHistory;
