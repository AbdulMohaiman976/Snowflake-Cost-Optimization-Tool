import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion } from 'framer-motion';
import { 
  BookOpen, 
  Search, 
  Database,
  ArrowRight,
  TrendingUp,
  Clock,
  Terminal,
  User,
  ExternalLink,
  Plus,
  Sparkles
} from 'lucide-react';

const Notebooks = () => {
    const { session } = useAuth();
    const notebooks = session?.notebooks || {};
    const items = notebooks.notebooks || [];

    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs] = useState('');

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'notebooks');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Failed to generate prescriptive SQL steps.');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-8"
        >
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">Notebooks</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Visibility into Snowflake Notebook execution, Python workloads, and data science compute resources.</p>
                </div>
                <div className="flex gap-4 p-4 bg-sidebar/50 border border-border rounded-xl">
                  <div className="pr-6 border-r border-border/50">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Total Executions</p>
                    <p className="text-xl font-black text-white font-mono">{notebooks.total_runs || 0}</p>
                  </div>
                  <div className="pl-2">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Compute Used (h)</p>
                    <p className="text-xl font-black text-primary-light font-mono">1.2h</p>
                  </div>
                </div>
            </div>

            <div className="glass-card p-6 bg-primary/5 border border-dashed border-primary/30 flex flex-col items-start gap-4 mb-8">
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

            <div className="grid grid-cols-1 gap-4">
                {items.length > 0 ? (
                    items.map((nb, idx) => (
                        <div key={idx} className="glass-card p-6 flex flex-col gap-5 group hover:border-primary/40 transition-colors relative">
                            <div className="absolute top-6 right-6 flex gap-2">
                                <button className="p-2 hover:bg-white/5 border border-border rounded-lg text-text-muted transition-colors"><ExternalLink className="w-4 h-4" /></button>
                                <button className="px-4 py-2 bg-primary/10 hover:bg-primary/20 border border-primary/20 text-primary-light text-[10px] font-black uppercase rounded-lg transition-all">Open Notebook</button>
                            </div>
                            <div className="flex items-start gap-6">
                                <div className="p-3 bg-sidebar border border-border rounded-2xl text-text-muted group-hover:text-primary-light group-hover:bg-primary/5 transition-all">
                                    <BookOpen className="w-7 h-7" strokeWidth={1} />
                                </div>
                                <div className="flex-1 space-y-4">
                                    <div className="flex flex-col">
                                        <h3 className="text-base font-bold text-white mb-0.5 tracking-tight">Snowpark ML Training</h3>
                                        <div className="flex items-center gap-2 text-[10px] text-text-muted font-bold uppercase tracking-widest">
                                            <span className="flex items-center gap-1"><User className="w-3 h-3" /> {nb.user}</span>
                                            <span className="w-1 h-1 bg-border rounded-full"></span>
                                            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(nb.date).toLocaleDateString()}</span>
                                            <span className="w-1 h-1 bg-border rounded-full"></span>
                                            <span className="flex items-center gap-1"><Database className="w-3 h-3" /> {nb.warehouse}</span>
                                        </div>
                                    </div>
                                    <div className="bg-[#0b1220] rounded-xl border border-border/40 p-4 relative overflow-hidden group/code cursor-pointer flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                          <div className="p-1 px-2 border border-primary/20 bg-primary/10 rounded font-mono text-[9px] text-primary-light font-black uppercase">PYTHON</div>
                                          <code className="text-xs font-mono text-text-accent block truncate max-w-lg">{nb.query}</code>
                                        </div>
                                        <div className="bg-primary/5 p-1 rounded-md border border-primary/20 opacity-0 group-hover/code:opacity-100 transition-opacity"><Plus className="w-4 h-4 text-primary-light" /></div>
                                    </div>
                                    <div className="flex items-center gap-10">
                                        <div className="flex flex-col">
                                            <span className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">Execution Time</span>
                                            <span className="text-sm font-bold text-white font-mono">{nb.exec_sec?.toFixed(1)}s</span>
                                        </div>
                                        <div className="flex flex-col border-l border-border pl-6">
                                            <span className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">Compute Spilled</span>
                                            <span className="text-sm font-bold text-white font-mono">{nb.spill_gb?.toFixed(2)} GB</span>
                                        </div>
                                        <div className="flex flex-col border-l border-border pl-6">
                                            <span className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">Cost Insight</span>
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-2 h-2 bg-success rounded-full"></div>
                                                <span className="text-[10px] font-bold text-success uppercase tracking-widest leading-none">Highly Efficient</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="p-20 glass-card border-dashed flex flex-col items-center justify-center text-center">
                        <div className="p-5 bg-white/5 border border-white/10 rounded-full mb-6">
                            <BookOpen className="w-12 h-12 text-white/20" strokeWidth={1} />
                        </div>
                        <h4 className="text-xl font-bold text-white mb-2 tracking-tight">No Snowpark Notebooks Detected</h4>
                        <p className="text-text-muted max-w-sm text-sm">Your Snowflake environment hasn't executed any notebook workloads in the selected time period.</p>
                        <button className="mt-6 px-6 py-2.5 bg-primary hover:bg-primary-dark text-white text-xs font-bold rounded-xl transition-all shadow-lg shadow-primary/25">Learn about Notebooks</button>
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default Notebooks;
