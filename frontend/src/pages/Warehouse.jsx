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
  Tooltip, 
  ResponsiveContainer,
  Cell,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  ZAxis,
  ComposedChart,
  LabelList,
  ReferenceLine
} from 'recharts';
import { 
  ChevronRight,
  X,
  Copy,
  Terminal,
  ExternalLink,
  Info,
  Sparkles,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';

const Warehouse = () => {
    const [selectedAlert, setSelectedAlert] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [copied, setCopied] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);
    const [agentPlan, setAgentPlan] = useState('');
    const [isAiExpanded, setIsAiExpanded] = useState(true);
    const [runtimeAiRecs, setRuntimeAiRecs] = useState('');

    const { session } = useAuth();
    const wh = session?.warehouse || {};
    const warehouses = wh.warehouses || [];
    const aiRecs = session?.ai_recommendations?.warehouse || {};

    const handleApplySolution = async (alert) => {
        setSelectedAlert(alert);
        setIsModalOpen(true);
        setAgentPlan('');
        
        if (!alert.fix_sql) {
            setIsGenerating(true);
            try {
                const res = await generateAgentPlan(session?.session_id, 'warehouse');
                setAgentPlan(res.plan);
            } catch (err) {
                setAgentPlan('-- LLM API Error: Failed to generate prescriptive SQL steps.');
            } finally {
                setIsGenerating(false);
            }
        }
    };

    const handleGenerateIntelligence = async () => {
        if (isGenerating) return;
        setIsGenerating(true);
        setRuntimeAiRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'warehouse');
            setRuntimeAiRecs(res.plan);
            setIsAiExpanded(true);
        } catch (err) {
            console.error('AI Gen Error:', err);
        } finally {
            setIsGenerating(false);
        }
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const chartData = (warehouses || []).map(w => ({
        name: w?.warehouse || 'N/A',
        credits: w?.credits || 0,
        action: w?.action || 'OK',
        type: w?.type || 'Standard',
        queue: w?.queue_pct || 0,
        spill: w?.spill_remote_pct || 0,
    })).sort((a, b) => b.credits - a.credits);

    const getActionColor = (action) => {
        switch (action) {
            case 'UPSIZE': return 'text-danger bg-danger/10 border-danger/20';
            case 'CONSIDER_UPSIZE': return 'text-warning bg-warning/10 border-warning/20';
            case 'CONSIDER_DOWNSIZE': return 'text-primary bg-primary/10 border-primary/20';
            case 'OK': return 'text-success bg-success/10 border-success/20';
            default: return 'text-text-muted bg-sidebar border-border';
        }
    };

    const getActionLabel = (action) => {
        switch (action) {
            case 'UPSIZE': return '🔴 High Priority Upsize';
            case 'CONSIDER_UPSIZE': return '🟡 Consider Upsizing';
            case 'CONSIDER_DOWNSIZE': return '🔵 Opportunity to Downsize';
            case 'OK': return '🟢 Optimized Performance';
            default: return '⚪ Manual Review Recommended';
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
                  <h1 className="text-3xl font-extrabold tracking-tight text-text mb-2">Warehouse Analytics</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Real-time analysis of warehouse sizing, queuing patterns, and credit consumption.</p>
                </div>
                <div className="p-3 bg-primary/5 border border-primary/20 rounded-2xl flex items-center gap-4">
                  <div className="px-4 border-r border-border">
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-[0.15em] mb-0.5">Total Credits (30d)</div>
                    <div className="text-lg font-bold text-text font-mono">{wh.total_credits?.toFixed(2)}</div>
                  </div>
                  <div className="px-4 border-r border-border">
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-[0.15em] mb-0.5">Active Warehouses</div>
                    <div className="text-lg font-bold text-text font-mono">{warehouses.length}</div>
                  </div>
                  <div className="px-4">
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-[0.15em] mb-0.5">Detected Issues</div>
                    <div className={`text-lg font-bold font-mono ${(aiRecs?.layer1?.alerts || []).length > 0 ? 'text-danger' : 'text-success'}`}>
                        {(aiRecs?.layer1?.alerts || []).length}
                    </div>
                  </div>
                </div>
            </div>

            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-border bg-sidebar/30 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-text uppercase tracking-widest">Warehouse Performance Registry</h3>
                  <div className="flex items-center gap-2">
                    <span className="p-1 px-2.5 rounded-lg bg-black/5 border border-black/10 text-[10px] font-extrabold text-text-muted uppercase">ROWS: {warehouses.length}</span>
                    <button className="p-1.5 rounded-lg hover:bg-black/5 border border-border text-text-muted"><Info className="w-4 h-4" /></button>
                  </div>
                </div>
                
                <div className="overflow-x-auto overflow-y-auto max-h-[500px]">
                    <table className="w-full text-left border-collapse table-fixed min-w-[800px]">
                        <thead>
                            <tr className="bg-black/30 text-[10px] font-bold text-text-muted uppercase tracking-widest border-b border-border sticky top-0 z-10">
                                <th className="px-4 py-4 font-bold w-[35%]">Warehouse Name</th>
                                <th className="px-4 py-4 font-bold w-[12%]">Size</th>
                                <th className="px-4 py-4 font-bold text-right w-[12%]">Credits</th>
                                <th className="px-4 py-4 font-bold text-right w-[13%]">Queue %</th>
                                <th className="px-4 py-4 font-bold w-[20%]">Recommendation</th>
                                <th className="px-4 py-4 text-right w-[8%]"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                            {warehouses.map((w, idx) => (
                                <tr key={idx} className="group hover:bg-black/[0.02] transition-colors">
                                    <td className="px-4 py-3">
                                        <div className="flex flex-col max-w-[280px]">
                                            <span className="text-xs font-bold text-text group-hover:text-primary flex items-center gap-2 truncate" title={w.warehouse}>
                                                {w.warehouse}
                                                {w.type === 'User Warehouse' && <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0"></span>}
                                            </span>
                                            <span className={`text-[9px] font-mono uppercase tracking-tighter ${w.type?.includes('System') ? 'text-warning/60' : 'text-text-muted'}`}>{w.type}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase transition-colors ${w.current_size === 'X-Small' ? 'bg-sidebar text-text-muted border border-border' : 'bg-primary/20 text-primary border border-primary/20'}`}>
                                            {w.current_size}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right font-mono text-xs text-text-accent font-bold">
                                        {w.credits?.toFixed(2)}
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <div className="w-12 h-1 bg-sidebar rounded-full overflow-hidden border border-border">
                                                <div className={`h-full bg-${w.queue_pct > 15 ? 'danger' : w.queue_pct > 5 ? 'warning' : 'success'}`} style={{ width: `${Math.min(w.queue_pct, 100)}%` }}></div>
                                            </div>
                                            <span className={`text-[9px] font-bold ${w.queue_pct > 15 ? 'text-danger' : 'text-text-muted'}`}>{w.queue_pct?.toFixed(0)}%</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className={`px-2 py-1 rounded-lg border text-[9px] font-bold w-fit ${getActionColor(w.action)}`}>
                                            {getActionLabel(w.action)}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <button 
                                            onClick={() => {
                                                const relatedAlert = (aiRecs?.layer1?.alerts || []).find(a => a.title.includes(w.warehouse));
                                                handleApplySolution(relatedAlert || {
                                                    title: `Optimize ${w.warehouse}`,
                                                    detail: `Standard optimization for ${w.current_size} warehouse.`,
                                                    fix_sql: `-- Check current configuration\nSHOW WAREHOUSES LIKE '${w.warehouse}';\n\n-- Recommended optimization\nALTER WAREHOUSE ${w.warehouse} SET AUTO_SUSPEND = 60;\nALTER WAREHOUSE ${w.warehouse} SET AUTO_RESUME = TRUE;`,
                                                    severity: 'MEDIUM'
                                                });
                                            }}
                                            className="text-[10px] font-black text-primary hover:text-text transition-colors"
                                        >
                                            FIX
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
                <div className="glass-card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h3 className="text-sm font-bold text-text uppercase tracking-widest">Credits by Warehouse</h3>
                        </div>
                    </div>
                    
                    <div className="h-[200px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} layout="vertical">
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" width={100} fontSize={9} stroke="#4b5563" axisLine={false} tickLine={false} />
                                <Bar dataKey="credits" radius={[0, 4, 4, 0]} barSize={14}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.credits > 100 ? '#ef4444' : '#2563eb'} fillOpacity={0.8} />
                                    ))}
                                </Bar>
                                <Tooltip contentStyle={{ backgroundColor: '#B7ECF9', border: '1px solid #1a2e4a', borderRadius: '8px', fontSize: '10px' }} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="glass-card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-text uppercase tracking-widest">Queue vs Spill Rate</h3>
                    </div>
                    <div className="h-[220px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f2937" />
                                <XAxis type="number" dataKey="queue" name="Queue %" unit="%" stroke="#4b5563" fontSize={9} domain={[0, 'auto']} />
                                <YAxis type="number" dataKey="spill" name="Spill %" unit="%" stroke="#4b5563" fontSize={9} domain={[0, 'auto']} />
                                <ZAxis type="number" range={[100, 800]} />
                                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#B7ECF9', border: '1px solid #1a2e4a', borderRadius: '8px', fontSize: '10px' }} />
                                <ReferenceLine x={10} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'QUEUE RISK', position: 'top', fill: '#ef4444', fontSize: 7, fontWeight: 'bold' }} />
                                <ReferenceLine y={5} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'SPILL RISK', position: 'right', fill: '#f59e0b', fontSize: 7, fontWeight: 'bold' }} />
                                <Scatter name="Warehouses" data={chartData} fill="#10b981" />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
                <div className={`glass-card overflow-hidden transition-all duration-500 border-l-[6px] border-primary ${isAiExpanded ? 'bg-primary/5 shadow-xl' : 'bg-sidebar/40 shadow-sm'}`}>
                    <div 
                        onClick={() => setIsAiExpanded(!isAiExpanded)}
                        className="p-6 cursor-pointer flex items-center justify-between group"
                    >
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-xl transition-all ${isAiExpanded ? 'bg-primary text-background' : 'bg-primary/10 text-primary'}`}>
                                <Sparkles className={`w-5 h-5 ${isGenerating ? 'animate-spin' : ''}`} />
                            </div>
                            <div>
                                <h3 className="text-sm font-black text-text uppercase tracking-[0.2em]">AI Actionable Intelligence</h3>
                                <p className="text-[10px] text-text-muted/60 font-bold uppercase mt-0.5">prescriptive optimization engine</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            {!runtimeAiRecs && !session?.ai_recommendations?.warehouse?.layer4?.recommendations_md && (
                                <button 
                                    onClick={(e) => { e.stopPropagation(); handleGenerateIntelligence(); }}
                                    className="px-4 py-1.5 bg-primary/20 hover:bg-primary/30 border border-primary/30 rounded-lg text-[10px] font-black text-primary uppercase tracking-widest transition-all"
                                >
                                    {isGenerating ? 'Analyzing...' : 'Generate Insights'}
                                </button>
                            )}
                            <ChevronRight className={`w-5 h-5 text-text-muted transition-transform duration-300 ${isAiExpanded ? 'rotate-90' : ''}`} />
                        </div>
                    </div>

                    <AnimatePresence>
                        {isAiExpanded && (
                            <motion.div 
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.4, ease: "circOut" }}
                            >
                                <div className="p-8 pt-0 space-y-8">
                                    {(runtimeAiRecs || session?.ai_recommendations?.warehouse?.layer4?.recommendations_md) ? (
                                        <div className="p-6 bg-background/50 border border-border/50 rounded-2xl relative overflow-hidden group">
                                            <div className="absolute top-0 right-0 p-2 opacity-5"><Sparkles className="w-16 h-16 text-primary" /></div>
                                            <p className="text-[10px] font-black text-primary uppercase tracking-[0.25em] mb-4 flex items-center gap-2">
                                                <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                                                Groq Synthesis Analysis
                                            </p>
                                            <div className="text-sm text-text font-medium whitespace-pre-wrap leading-relaxed max-h-[400px] overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-primary/20">
                                                {runtimeAiRecs || session.ai_recommendations.warehouse.layer4.recommendations_md}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="p-12 flex flex-col items-center justify-center text-center bg-black/5 border border-dashed border-border rounded-2xl">
                                            <Sparkles className="w-10 h-10 text-text-muted/20 mb-4" />
                                            <p className="text-xs font-bold text-text-muted uppercase tracking-widest">No active intelligence generated for this node</p>
                                            <button 
                                                onClick={handleGenerateIntelligence}
                                                className="mt-6 px-8 py-3 bg-primary text-background font-black text-xs uppercase tracking-widest rounded-xl hover:scale-105 transition-all shadow-lg"
                                            >
                                                Initialize AI Analysis
                                            </button>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-3 gap-6">
                                        {(aiRecs?.layer1?.alerts || []).slice(0, 3).map((alert, i) => (
                                            <div key={i} className="group/alert p-5 bg-background/40 border border-border/50 rounded-2xl flex flex-col justify-between hover:border-primary/40 hover:bg-background transition-all shadow-sm">
                                                <div>
                                                    <div className={`text-[9px] font-black uppercase mb-3 flex items-center gap-1.5 ${alert.severity === 'HIGH' ? 'text-danger' : 'text-warning'}`}>
                                                        <div className={`w-1.5 h-1.5 rounded-full ${alert.severity === 'HIGH' ? 'bg-danger' : 'bg-warning'} animate-pulse`}></div>
                                                        {alert.severity} PRIORITY
                                                    </div>
                                                    <p className="text-sm font-bold text-text mb-3 group-hover/alert:text-primary transition-colors">{alert.title}</p>
                                                    <div className="p-4 bg-primary/5 rounded-xl mb-4 border-l-2 border-primary/20">
                                                        <p className="text-[10px] text-primary/60 font-black mb-1 uppercase tracking-wider">Optimization Hint:</p>
                                                        <p className="text-[11px] text-text-muted leading-relaxed font-medium italic">{alert.detail}</p>
                                                    </div>
                                                </div>
                                                <button 
                                                    onClick={() => handleApplySolution(alert)}
                                                    className="mt-2 text-[10px] font-black text-primary uppercase tracking-widest hover:text-text transition-colors flex items-center gap-1.5 group/btn"
                                                >
                                                    Apply Solution <ChevronRight className="w-3.5 h-3.5 transition-transform group-hover/btn:translate-x-1" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
            <AnimatePresence>
                {isModalOpen && selectedAlert && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsModalOpen(false)}
                            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
                        />
                        <motion.div 
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="relative w-full max-w-2xl bg-sidebar border border-border rounded-2xl shadow-2xl overflow-hidden"
                        >
                            <div className="p-6 border-b border-border flex items-center justify-between bg-black/30">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${selectedAlert.severity === 'HIGH' ? 'bg-danger/10 text-danger' : 'bg-warning/10 text-warning'}`}>
                                        <Sparkles className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-text">{selectedAlert.title}</h3>
                                        <p className="text-xs text-text-muted">Prescriptive Optimization Solution</p>
                                    </div>
                                </div>
                                <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-black/5 rounded-lg text-text-muted transition-colors">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="p-8 space-y-6">
                                <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 p-1.5 px-3 bg-primary/10 text-[9px] font-black text-primary uppercase tracking-[0.2em] rounded-bl-xl border-l border-b border-primary/20">AI STRATEGIC INSIGHT</div>
                                    <div className="flex items-start gap-4">
                                        <div className="mt-1 p-2 bg-primary/10 rounded-lg text-primary">
                                            <Sparkles className="w-4 h-4" />
                                        </div>
                                        <div>
                                            <h4 className="text-[10px] font-black text-text/40 uppercase tracking-[0.15em] mb-1">Recommendation</h4>
                                            <p className="text-sm text-text font-medium leading-relaxed">
                                                {selectedAlert.detail}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 text-text-accent">
                                            <Terminal className="w-3.5 h-3.5" />
                                            <h4 className="text-[10px] font-black uppercase tracking-widest">TECHNICAL IMPLEMENTATION</h4>
                                        </div>
                                        <button 
                                            onClick={() => copyToClipboard(selectedAlert.fix_sql)}
                                            className="flex items-center gap-2 text-[10px] font-bold text-text-muted hover:text-text transition-colors py-1 px-2 rounded-lg hover:bg-black/5"
                                        >
                                            {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                                            {copied ? 'COPIED' : 'COPY SQL'}
                                        </button>
                                    </div>
                                    <div className="relative group">
                                        <div className="absolute inset-0 bg-primary/5 rounded-xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                                        <pre className="relative p-6 bg-background/50 border border-border rounded-xl font-mono text-xs text-text-accent leading-relaxed overflow-x-auto min-h-[120px]">
                                            {isGenerating ? (
                                                <span className="animate-pulse text-primary">Generating real-time SQL fix via Groq API...</span>
                                            ) : (
                                                <code>{selectedAlert.fix_sql || agentPlan || session?.ai_recommendations?.warehouse?.layer4?.recommendations_md || '-- No specific SQL fix required for this alert.'}</code>
                                            )}
                                        </pre>
                                    </div>
                                </div>

                                <div className="pt-4 flex items-center gap-4">
                                    <button 
                                        onClick={() => setIsModalOpen(false)}
                                        className="flex-1 py-3 px-4 bg-primary text-background font-black text-xs uppercase tracking-widest rounded-xl hover:bg-primary-light transition-colors flex items-center justify-center gap-2"
                                    >
                                        <ExternalLink className="w-4 h-4" /> Execute in Snowflake Worksheets
                                    </button>
                                    <button 
                                        onClick={() => setIsModalOpen(false)}
                                        className="px-6 py-3 border border-border text-text font-black text-xs uppercase tracking-widest rounded-xl hover:bg-black/5 transition-colors"
                                    >
                                        Closed
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default Warehouse;
