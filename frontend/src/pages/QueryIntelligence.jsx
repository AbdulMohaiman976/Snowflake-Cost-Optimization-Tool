import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';
import { 
  Search, 
  Clock, 
  Zap, 
  Terminal, 
  Database, 
  Filter, 
  ChevronRight, 
  CheckCircle2, 
  AlertTriangle,
  FileCode,
  Flame,
  ArrowUpRight,
  Layers,
  TrendingUp,
  TrendingDown,
  Sparkles
} from 'lucide-react';

const QueryItem = ({ query }) => {
    const [expanded, setExpanded] = useState(false);
    const tagColor = {
        'OK': 'bg-success/10 text-success border-success/20',
        'SLOW QUERY': 'bg-danger/10 text-danger border-danger/20',
        'HIGH REMOTE SPILL': 'bg-danger/20 text-danger border-danger/40',
        'POOR PRUNING': 'bg-warning/10 text-warning border-warning/20',
        'QUEUE BOTTLENECK': 'bg-warning/20 text-warning border-warning/40'
    }[query.problem_tag] || 'bg-sidebar/50 text-text-muted border-border';

    const getIcon = (tag) => {
        if (tag === 'OK') return <CheckCircle2 className="w-3.5 h-3.5 text-success" />;
        if (tag === 'SLOW QUERY') return <Flame className="w-3.5 h-3.5 text-danger" />;
        return <AlertTriangle className="w-3.5 h-3.5 text-warning" />;
    };

    return (
        <div className="border border-border rounded-xl bg-sidebar/30 hover:bg-sidebar/50 transition-all overflow-hidden group">
            <div 
                className="p-5 flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-6 flex-1">
                    <div className="p-2.5 bg-background border border-border rounded-lg group-hover:border-primary/50 transition-colors">
                        <Terminal className="w-4.5 h-4.5 text-primary-light" />
                    </div>
                    <div className="max-w-md">
                        <div className="flex items-center gap-3 mb-1">
                          <p className="text-sm font-bold text-white font-mono truncate max-w-[200px]">{query.query_id}</p>
                          <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border flex items-center gap-1.5 ${tagColor}`}>
                            {getIcon(query.problem_tag)}
                            {query.problem_tag}
                          </div>
                        </div>
                        <p className="text-xs text-text-muted truncate max-w-[400px]">{query.query_text}</p>
                    </div>
                </div>

                <div className="flex items-center gap-8 pr-4">
                    <div className="text-right">
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-0.5">Execution</p>
                        <p className={`text-sm font-bold font-mono ${query.exec_seconds > 60 ? 'text-danger' : 'text-text-accent'}`}>{query.exec_seconds}s</p>
                    </div>
                    <div className="text-right">
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-0.5">Scanned</p>
                        <p className="text-sm font-bold font-mono text-white">{query.scan_pct?.toFixed(1)}%</p>
                    </div>
                    <ChevronRight className={`w-5 h-5 text-text-muted transition-transform duration-300 ${expanded ? 'rotate-90 text-primary-light' : ''}`} />
                </div>
            </div>

            <AnimatePresence>
                {expanded && (
                    <motion.div 
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        className="overflow-hidden bg-background/50 border-t border-border"
                    >
                        <div className="p-6 space-y-5">
                            {query.tag && query.tag !== 'OK' && (
                                <div className="p-4 bg-danger/5 border border-danger/20 rounded-xl flex items-start gap-3">
                                    <div className="p-1.5 bg-danger/10 rounded-lg shrink-0 mt-0.5">
                                        <AlertTriangle className="w-4 h-4 text-danger" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-danger/70 uppercase tracking-widest mb-1">Root Cause — {query.tag}</p>
                                        <p className="text-sm text-white/80 leading-relaxed">{getReason(query.tag)}</p>
                                    </div>
                                </div>
                            )}

                            <div className="grid grid-cols-4 gap-4">
                                <div className="p-3 bg-sidebar/40 border border-border rounded-xl">
                                    <p className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">Execution Time</p>
                                    <p className={`text-lg font-extrabold font-mono ${query.exec_sec > 60 ? 'text-danger' : 'text-white'}`}>{query.duration || `${query.exec_sec}s`}</p>
                                </div>
                                <div className="p-3 bg-sidebar/40 border border-border rounded-xl">
                                    <p className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">Data Spilled</p>
                                    <p className={`text-lg font-extrabold font-mono ${query.spill_gb > 0 ? 'text-warning' : 'text-success'}`}>{query.spill_gb?.toFixed(3) || '0.000'} GB</p>
                                </div>
                                <div className="p-3 bg-sidebar/40 border border-border rounded-xl">
                                    <p className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">Queued</p>
                                    <p className="text-lg font-extrabold font-mono text-white">{query.queued_sec?.toFixed(1) || '0.0'}s</p>
                                </div>
                                <div className="p-3 bg-sidebar/40 border border-border rounded-xl">
                                    <p className="text-[9px] text-text-muted font-black uppercase tracking-widest mb-1">Partition Pruning</p>
                                    <p className={`text-lg font-extrabold font-mono ${(query.pruning_pct || 100) < 50 ? 'text-danger' : 'text-success'}`}>{query.pruning_pct?.toFixed(1) || '100.0'}%</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div className="p-4 bg-sidebar/30 border border-border rounded-xl space-y-3">
                                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Context</p>
                                    <div className="space-y-2 text-xs">
                                        <div className="flex justify-between gap-2"><span className="text-text-muted">User</span><span className="font-bold text-white truncate">{query.user || '—'}</span></div>
                                        <div className="flex justify-between gap-2"><span className="text-text-muted">Warehouse</span><span className="font-bold text-primary-light uppercase text-[10px] truncate">{query.warehouse || '—'}</span></div>
                                        <div className="flex justify-between gap-2"><span className="text-text-muted shrink-0">Run At</span><span className="font-bold text-text-accent text-[10px] truncate">{query.start_time || '—'}</span></div>
                                    </div>
                                </div>
                                <div className="col-span-2 bg-[#0b1220] rounded-xl border border-border/50 p-4 font-mono text-xs text-text-accent leading-relaxed relative overflow-hidden">
                                    <div className="absolute top-0 right-0 p-2 text-[10px] text-primary/40 font-bold uppercase tracking-widest border-l border-b border-border bg-sidebar/50">SQL SOURCE</div>
                                    <code className="block whitespace-pre-wrap pt-4">{query.query || '(system internal)'}</code>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};


const QueryIntelligence = () => {
    const { session } = useAuth();
    const qry = session?.queries || {};
    const topQueries = qry.queries || [];

    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs] = useState('');

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'queries');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Failed to generate prescriptive SQL steps.');
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
                  <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">Query Intelligence</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Deep analysis of workload patterns, slow running tasks, and resource-heavy executions.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                        <input className="bg-sidebar border border-border rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-primary/50 transition-all w-[300px]" placeholder="Search Query ID, User, or SQL..." />
                    </div>
                    <button className="p-2.5 bg-sidebar-item border border-border rounded-xl hover:bg-white/5 transition-all"><Filter className="w-5 h-5 text-text-muted" /></button>
                </div>
            </div>

            <div className="grid grid-cols-4 gap-6 mb-8">
                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-primary/10 border border-primary/20 rounded-lg w-fit mb-4">
                            <Layers className="w-5 h-5 text-primary-light" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1">Total Queries</p>
                        <h4 className="text-2xl font-extrabold text-white">{qry.total || 0}</h4>
                    </div>
                    <div className="text-[10px] text-success font-bold flex items-center gap-1">
                        <TrendingUp className="w-3.5 h-3.5" /> +12.5% increase
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-success/10 border border-success/20 rounded-lg w-fit mb-4">
                            <Clock className="w-5 h-5 text-success" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1">Avg Execution</p>
                        <h4 className="text-2xl font-extrabold text-white">{qry.avg_exec?.toFixed(1) || '0.0'}s</h4>
                    </div>
                    <div className="text-[10px] text-success font-bold flex items-center gap-1">
                        <TrendingDown className="w-3.5 h-3.5" /> -0.8s faster
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-warning/10 border border-warning/20 rounded-lg w-fit mb-4">
                            <AlertTriangle className="w-5 h-5 text-warning" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1">Detected Issues</p>
                        <h4 className="text-2xl font-extrabold text-white">{qry.problem_count || 0}</h4>
                    </div>
                    <div className="text-[10px] text-danger font-bold flex items-center gap-1">
                        <ArrowUpRight className="w-3.5 h-3.5" /> 8 new detections
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-primary/10 border border-primary/20 rounded-lg w-fit mb-4">
                            <Database className="w-5 h-5 text-primary-light" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1">Compute Spilled</p>
                        <h4 className="text-2xl font-extrabold text-white">{qry.total_spill_gb?.toFixed(1) || '0.0'} GB</h4>
                    </div>
                    <div className="text-[10px] text-warning font-bold flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> High remote spike
                    </div>
                </div>
            </div>

            <div className="glass-card p-6 space-y-6 mb-8">
                <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest">Slowest Running Tasks (Last 24h)</h3>
                    <p className="text-[10px] text-text-muted/60 font-bold uppercase tracking-[0.1em]">Sort by: Execution Time</p>
                </div>
                
                <div className="space-y-6">
                    {topQueries.length > 0 ? (
                        <>
                            <div className="h-64 w-full bg-background/50 border border-border rounded-xl p-4">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={topQueries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                        <XAxis 
                                            dataKey="query_id" 
                                            stroke="#ffffff40" 
                                            fontSize={10} 
                                            tickLine={false} 
                                            axisLine={false}
                                            tickFormatter={(val) => val.substring(0, 8) + '...'}
                                        />
                                        <YAxis 
                                            stroke="#ffffff40" 
                                            fontSize={10} 
                                            tickLine={false} 
                                            axisLine={false}
                                            tickFormatter={(val) => `${val}s`}
                                        />
                                        <RechartsTooltip 
                                            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                            itemStyle={{ color: '#fff', fontSize: '12px', fontWeight: 'bold' }}
                                            formatter={(value) => [`${value}s`, 'Execution Time']}
                                            labelStyle={{ color: '#94a3b8', fontSize: '10px', marginBottom: '4px' }}
                                        />
                                        <Bar dataKey="exec_sec" radius={[4, 4, 0, 0]}>
                                            {topQueries.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.tag === 'OK' ? '#2563eb' : '#ef4444'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="space-y-4">
                                {topQueries.map((query, idx) => (
                                    <QueryItem key={idx} query={query} />
                                ))}
                            </div>
                        </>
                    ) : (
                        <div className="p-12 border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-center">
                            <div className="p-4 bg-white/5 border border-white/10 rounded-full mb-6">
                                <Search className="w-10 h-10 text-white/20" strokeWidth={1} />
                            </div>
                            <h4 className="text-xl font-bold text-white mb-2">No heavy queries found</h4>
                            <p className="text-text-muted max-w-xs text-sm">Your Snowflake instance seems to be running efficient workloads tonight.</p>
                        </div>
                    )}
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
        </motion.div>
    );
};

export default QueryIntelligence;
