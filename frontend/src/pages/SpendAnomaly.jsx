import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion } from 'framer-motion';
import { 
  AreaChart,
  Area,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  Legend
} from 'recharts';
import { 
  AlertTriangle, 
  ShieldCheck, 
  TrendingUp, 
  Calendar,
  Layers,
  Sparkles,
  CheckCircle2,
  Info
} from 'lucide-react';

const ShieldAlert = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
    <path d="M12 8v4" /><path d="M12 16h.01" />
  </svg>
);

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-[#0f172a] border border-white/10 rounded-xl p-3 shadow-2xl min-w-[180px]">
      <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-2">{label}</p>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center justify-between gap-4 text-xs">
          <span style={{ color: p.color }} className="font-bold">{p.name}</span>
          <span className="font-mono font-bold text-white">{p.value?.toFixed(4)}</span>
        </div>
      ))}
    </div>
  );
};

const SpendAnomaly = () => {
    const { session } = useAuth();
    const anomaly = session?.anomaly || {};
    
    // Correct backend fields
    const dailyList   = anomaly.daily         || [];
    const anomalies   = anomaly.anomalies      || [];
    const recommendations = anomaly.recommendations || [];
    const anomalyCount = anomaly.anomaly_count  || 0;
    const warningCount = anomaly.warning_count  || 0;

    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs]   = useState('');

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'anomaly');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Could not generate anomaly remediation steps.');
        } finally {
            setIsGenerating(false);
        }
    };

    // Build chart data — group by date, aggregate credits across warehouses
    const chartDataMap = {};
    dailyList.forEach(d => {
        const key = d.label || d.date;
        if (!chartDataMap[key]) {
            chartDataMap[key] = { label: key, credits: 0, avg: d.avg, status: d.status };
        }
        chartDataMap[key].credits += d.credits;
    });
    const chartData = Object.values(chartDataMap).slice(-20);

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-8"
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">Spend Anomaly</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Early detection of credit spikes and unusual workload patterns before they impact your bill.</p>
                </div>
                <div className="flex gap-4">
                  <div className="p-4 bg-sidebar/50 border border-border rounded-xl">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-2 leading-none">Anomalies Detected</p>
                    <p className={`text-2xl font-black font-mono ${anomalyCount > 0 ? 'text-danger' : 'text-success'}`}>{anomalyCount}</p>
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">High Priority</p>
                  </div>
                  <div className="p-4 bg-sidebar/50 border border-border rounded-xl">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-2 leading-none">Warnings</p>
                    <p className={`text-2xl font-black font-mono ${warningCount > 0 ? 'text-warning' : 'text-success'}`}>{warningCount}</p>
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">Medium Priority</p>
                  </div>
                </div>
            </div>

            {/* Credit Spend Chart */}
            <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-base font-bold text-white mb-1">Credit Spend vs 7-Day Baseline</h3>
                        <p className="text-[11px] text-text-muted font-medium">Daily credits consumed compared to rolling average — spikes highlighted in red</p>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest">
                        <span className="flex items-center gap-1.5"><span className="w-3 h-1 bg-primary rounded-full inline-block"></span> Daily Credits</span>
                        <span className="flex items-center gap-1.5"><span className="w-3 h-1 bg-warning rounded-full inline-block"></span> 7-Day Avg</span>
                    </div>
                </div>
                {chartData.length > 0 ? (
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="creditsGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="avgGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.15}/>
                                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                                <XAxis dataKey="label" stroke="#ffffff30" fontSize={9} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                                <YAxis stroke="#ffffff30" fontSize={9} tickLine={false} axisLine={false} tickFormatter={v => v.toFixed(3)} />
                                <Tooltip content={<CustomTooltip />} />
                                <Area type="monotone" dataKey="avg"     name="7-Day Avg"      stroke="#f59e0b" strokeWidth={1.5} fill="url(#avgGrad)"     strokeDasharray="4 2" dot={false} />
                                <Area type="monotone" dataKey="credits" name="Daily Credits"  stroke="#2563eb" strokeWidth={2}   fill="url(#creditsGrad)" dot={(props) => {
                                    const { cx, cy, payload } = props;
                                    if (payload.status === 'ANOMALY') return <circle key={`dot-${cx}`} cx={cx} cy={cy} r={5} fill="#ef4444" stroke="#ef444480" strokeWidth={2} />;
                                    if (payload.status === 'WARNING') return <circle key={`dot-${cx}`} cx={cx} cy={cy} r={4} fill="#f59e0b" stroke="#f59e0b80" strokeWidth={2} />;
                                    return null;
                                }} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="h-64 flex items-center justify-center border border-dashed border-border rounded-xl">
                        <div className="text-center">
                            <TrendingUp className="w-10 h-10 text-white/10 mx-auto mb-3" strokeWidth={1} />
                            <p className="text-text-muted text-sm">No daily spend data available</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Anomaly List + Sidebar */}
            <div className="grid grid-cols-3 gap-6">
                <div className="col-span-2 glass-card p-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-sm font-bold text-white uppercase tracking-widest">Detected Anomalies & Warnings</h3>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">{anomalies.length} events</p>
                    </div>

                    {anomalies.length > 0 ? anomalies.map((item, idx) => (
                        <div key={idx} className="p-4 bg-sidebar/30 border border-border rounded-xl flex items-start justify-between gap-4 group hover:border-primary/30 transition-colors">
                            <div className="flex items-start gap-4 flex-1 min-w-0">
                                <div className={`p-2 rounded-lg shrink-0 mt-0.5 ${item.status === 'ANOMALY' ? 'bg-danger/10 border border-danger/20' : 'bg-warning/10 border border-warning/20'}`}>
                                    <AlertTriangle className={`w-4 h-4 ${item.status === 'ANOMALY' ? 'text-danger' : 'text-warning'}`} />
                                </div>
                                <div className="min-w-0">
                                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                                        <p className="text-sm font-bold text-white uppercase tracking-wide">{item.warehouse}</p>
                                        <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest border ${item.status === 'ANOMALY' ? 'bg-danger/10 border-danger/20 text-danger' : 'bg-warning/10 border-warning/20 text-warning'}`}>
                                            {item.status}
                                        </span>
                                    </div>
                                    <p className="text-[10px] text-text-muted flex items-center gap-1.5 mb-2">
                                        <Calendar className="w-3 h-3" /> {item.date} ({item.day_of_week})
                                    </p>
                                    <p className="text-[11px] text-text-muted/80 leading-relaxed">{item.possible_reasons?.join(' · ')}</p>
                                </div>
                            </div>
                            <div className="shrink-0 text-right space-y-2">
                                <div>
                                    <p className="text-[9px] text-text-muted font-black uppercase tracking-widest">Spike</p>
                                    <p className={`text-lg font-extrabold font-mono ${item.spike_ratio > 2 ? 'text-danger' : 'text-warning'}`}>{item.spike_ratio?.toFixed(2)}×</p>
                                </div>
                                <div>
                                    <p className="text-[9px] text-text-muted font-black uppercase tracking-widest">Credits</p>
                                    <p className="text-sm font-bold font-mono text-white">{item.credits?.toFixed(4)}</p>
                                </div>
                                <div>
                                    <p className="text-[9px] text-text-muted font-black uppercase tracking-widest">Est. Cost</p>
                                    <p className="text-sm font-bold font-mono text-danger">${item.est_cost_usd?.toFixed(3)}</p>
                                </div>
                            </div>
                        </div>
                    )) : (
                        <div className="p-12 border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-center">
                            <CheckCircle2 className="w-12 h-12 text-success/30 mb-4" strokeWidth={1} />
                            <p className="text-white font-bold mb-1">No anomalies detected</p>
                            <p className="text-text-muted text-sm max-w-xs">All daily credit usage is within the normal 7-day rolling average range.</p>
                        </div>
                    )}
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <div className="glass-card p-6 border-l-[4px] border-danger backdrop-blur-xl">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 bg-danger/10 rounded-lg">
                                <ShieldAlert className="w-5 h-5 text-danger" />
                            </div>
                            <h4 className="text-sm font-bold text-white uppercase tracking-widest">Urgent Advisory</h4>
                        </div>
                        <p className="text-xs text-text-muted leading-relaxed font-medium">
                            {anomalyCount > 0 
                                ? <><span className="text-danger font-bold">{anomalyCount} critical anomal{anomalyCount > 1 ? 'ies' : 'y'}</span> detected. Immediate review recommended to prevent cost overrun.</>
                                : warningCount > 0
                                    ? <><span className="text-warning font-bold">{warningCount} warning{warningCount > 1 ? 's' : ''}</span> detected. Spend trending above baseline — monitor closely.</>
                                    : <>All warehouses are within normal spend range. <span className="text-success font-bold">No action required.</span></>
                            }
                        </p>
                    </div>

                    <div className="glass-card p-6">
                        <div className="flex items-center gap-3 mb-5">
                            <div className="p-2 bg-primary/10 rounded-lg">
                                <Layers className="w-5 h-5 text-primary-light" />
                            </div>
                            <h4 className="text-sm font-bold text-white uppercase tracking-widest">Pattern Recognition</h4>
                        </div>
                        <div className="space-y-5">
                            <div>
                                <div className="flex items-center justify-between text-xs font-medium mb-2">
                                    <span className="text-text-muted">Workload Drift</span>
                                    <span className={`font-bold ${anomalyCount > 0 ? 'text-danger' : warningCount > 0 ? 'text-warning' : 'text-success'}`}>
                                        {anomalyCount > 0 ? 'Critical' : warningCount > 0 ? 'Elevated' : 'Stable'}
                                    </span>
                                </div>
                                <div className="h-1.5 w-full bg-sidebar border border-border rounded-full overflow-hidden">
                                    <div className={`h-full ${anomalyCount > 0 ? 'bg-danger' : warningCount > 0 ? 'bg-warning' : 'bg-success'}`}
                                         style={{ width: `${anomalyCount > 0 ? 90 : warningCount > 0 ? 55 : 15}%` }} />
                                </div>
                            </div>
                            <div>
                                <div className="flex items-center justify-between text-xs font-medium mb-2">
                                    <span className="text-text-muted">Cost Velocity</span>
                                    <span className={`font-bold ${(anomalyCount + warningCount) > 3 ? 'text-danger' : (anomalyCount + warningCount) > 0 ? 'text-warning' : 'text-success'}`}>
                                        {(anomalyCount + warningCount) > 3 ? 'Accelerating' : (anomalyCount + warningCount) > 0 ? 'Increasing' : 'Normal'}
                                    </span>
                                </div>
                                <div className="h-1.5 w-full bg-sidebar border border-border rounded-full overflow-hidden">
                                    <div className={`h-full ${(anomalyCount + warningCount) > 3 ? 'bg-danger' : (anomalyCount + warningCount) > 0 ? 'bg-warning' : 'bg-success'}`}
                                         style={{ width: `${Math.min((anomalyCount + warningCount) * 15 + 10, 95)}%` }} />
                                </div>
                            </div>
                            <div className="pt-3 border-t border-border">
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-text-muted">Total Events Analyzed</span>
                                    <span className="font-bold text-white font-mono">{dailyList.length}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* AI Actionable Block */}
            <div className="glass-card p-6 bg-primary/5 border border-dashed border-primary/30 flex flex-col items-start gap-4">
                <div className="flex justify-between items-center w-full">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/20 rounded-lg">
                            <Sparkles className="w-5 h-5 text-primary-light" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white uppercase tracking-widest leading-none mb-1">AI Anomaly Analysis</h3>
                            <p className="text-[10px] text-text-muted font-black uppercase tracking-widest">Runtime Prescriptive Intelligence — Anomaly &amp; Spend Rules</p>
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

export default SpendAnomaly;
