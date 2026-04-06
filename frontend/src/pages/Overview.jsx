import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, 
  TrendingUp, 
  AlertCircle, 
  Clock, 
  ArrowUpRight, 
  Target, 
  ShieldAlert,
  ArrowDownRight,
  Plus,
  Archive,
  Layers,
  Sparkles,
  CheckCircle,
  ArrowRight
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

const OverviewDataCard = ({ title, value, detail, icon: Icon, color, trend, onClick, isSelected }) => (
    <div 
        onClick={onClick}
        className={`glass-card p-6 flex items-start justify-between group overflow-hidden relative cursor-pointer border-t-4 transition-all hover:scale-[1.02] ${isSelected ? `border-${color} bg-white/[0.03]` : 'border-transparent'}`}
    >
        {/* Glow effect on hover */}
        <div className={`absolute top-0 right-0 w-32 h-32 opacity-0 group-hover:opacity-10 transition-opacity bg-${color} rounded-full blur-[40px] translate-x-10 -translate-y-10`}></div>
        
        <div>
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em] mb-4 block">{title}</span>
            <div className="flex items-baseline gap-2 mb-2">
                <h3 className="text-3xl font-extrabold text-white tracking-tight">{value}</h3>
                {trend !== undefined && (
                    <div className={`flex items-center gap-0.5 text-[11px] font-bold ${trend > 0 ? 'text-danger' : 'text-success'}`}>
                        {trend > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {Math.abs(trend)}%
                    </div>
                )}
            </div>
            <p className="text-xs text-text-muted/80 font-medium leading-relaxed max-w-[180px]">{detail}</p>
        </div>
        <div className={`p-4 bg-${color}/10 border border-${color}/20 rounded-2xl`}>
            <Icon className={`w-6 h-6 text-${color}`} strokeWidth={1.5} />
        </div>
    </div>
);

const Overview = () => {
    const { session } = useAuth();
    const health = session?.health || {};
    const warehouse = session?.warehouse || {};
    const savings = session?.savings || {};

    const healthColor = health.overall >= 75 ? 'success' : health.overall >= 50 ? 'warning' : 'danger';
    const [selectedTab, setSelectedTab] = useState('spend');
    const [isGenerating, setIsGenerating] = useState(false);
    const [runtimeRecs, setRuntimeRecs] = useState('');

    const aiRecs = runtimeRecs || session?.ai_recommendations?.anomaly?.layer4?.recommendations_md || session?.ai_recommendations?.anomaly?.layer1?.analysis || "Analyzing anomalous spend and optimizing your architecture based on current usage patterns...";

    const handleExecuteAdvice = async () => {
        setIsGenerating(true);
        setRuntimeRecs('');
        try {
            const res = await generateAgentPlan(session?.session_id, 'anomaly');
            setRuntimeRecs(res.plan);
        } catch (err) {
            setRuntimeRecs('-- LLM API Error: Failed to generate prescriptive SQL steps.');
        } finally {
            setIsGenerating(false);
        }
    };

    const dailyData = session?.cost?.daily || [];
    const chartData = dailyData.length > 0 
        ? dailyData.slice(-30).map(d => ({
            name: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            credits: d.credits || 0
        })) 
        : [];

    const calculateDailyTrend = () => {
        if (!dailyData || dailyData.length < 2) return 0;
        const last = dailyData[dailyData.length - 1].credits || 0;
        const prev = dailyData[dailyData.length - 2].credits || 0;
        if (prev === 0) return last > 0 ? 100 : 0;
        return Math.round(((last - prev) / prev) * 100);
    };

    const spendTrend = calculateDailyTrend();

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-8"
        >
            <div className="flex items-end justify-between">
                <div>
                  <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">Account Overview</h1>
                  <p className="text-text-muted max-w-lg leading-relaxed">Comprehensive health analysis across warehouses, queries, and storage systems.</p>
                </div>
            </div>

            <div className="grid grid-cols-4 gap-6">
                <div 
                    onClick={() => setSelectedTab('health')}
                    className={`p-8 glass-card border-l-[6px] border-${healthColor} bg-gradient-to-br from-sidebar to-background cursor-pointer transition-all ${selectedTab === 'health' ? 'ring-2 ring-primary/40 scale-[1.02]' : ''}`}
                >
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em] mb-4 block">Overall Health</span>
                    <div className="flex items-baseline gap-2 mb-2">
                        <h2 className={`text-6xl font-black text-white`}>{health?.overall || 0} <span className="text-xl text-text-muted/40 font-normal">/100</span></h2>
                    </div>
                    <div className="flex items-center gap-2 mt-4 px-3 py-1 bg-white/5 border border-white/10 rounded-full w-fit">
                        <div className={`w-2 h-2 rounded-full bg-${healthColor}`}></div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider text-${healthColor}`}>{health?.grade || 'N/A'}</span>
                    </div>
                </div>

                <OverviewDataCard 
                    title="Estimated Monthly Spend"
                    value={`$${(warehouse?.total_cost_usd || 0).toLocaleString()}`}
                    detail={`${(warehouse?.total_credits || 0).toFixed(2)} total credits used`}
                    icon={TrendingUp}
                    color="primary"
                    trend={spendTrend !== 0 ? spendTrend : undefined}
                    onClick={() => setSelectedTab('spend')}
                    isSelected={selectedTab === 'spend'}
                />

                <OverviewDataCard 
                    title="Optimization Potential"
                    value={`$${(savings?.total_usd || savings?.potential_savings || savings?.saving_usd || 0).toLocaleString()}`}
                    detail={`${savings?.item_count || 0} active savings opportunities detected`}
                    icon={Zap}
                    color="success"
                    onClick={() => setSelectedTab('savings')}
                    isSelected={selectedTab === 'savings'}
                />

                <OverviewDataCard 
                    title="Credits Spent (30 Days)"
                    value={(warehouse?.total_credits || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    detail="Total compute credits burned over the last 30 days"
                    icon={Zap}
                    color="primary"
                    onClick={() => setSelectedTab('spend')}
                    isSelected={selectedTab === 'spend'}
                />
            </div>

            <div className="grid grid-cols-3 gap-6">
                <div className="col-span-2 glass-card p-8">
                    <AnimatePresence mode="wait">
                        {selectedTab === 'health' && (
                            <motion.div key="health" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                <div className="mb-0">
                                    <h3 className="text-xl font-bold text-white mb-2 underline decoration-primary/30 underline-offset-8">Account Vitals Analysis</h3>
                                    <p className="text-xs text-text-muted leading-relaxed mb-6">Your score of <span className={`font-bold text-${healthColor}`}>{health?.overall}/100</span> is weighted by query speed and warehouse scaling.</p>
                                 </div>
                                 <div className="grid grid-cols-2 gap-8">
                                     <div className="space-y-4">
                                         <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Postures</p>
                                         <div className="space-y-4">
                                             {[
                                                 { name: 'Query Perf', score: health?.scores?.query || 0, color: 'primary' },
                                                 { name: 'Warehouse', score: health?.scores?.warehouse || 0, color: 'success' },
                                                 { name: 'Storage', score: health?.scores?.storage || 0, color: 'warning' },
                                             ].map((dim) => (
                                                 <div key={dim.name} className="space-y-1.5">
                                                     <div className="flex justify-between text-[10px] font-bold uppercase">
                                                         <span className="text-text-muted">{dim.name} Efficiency</span>
                                                         <span className="text-white">{dim.score}%</span>
                                                     </div>
                                                     <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                                        <div className={`h-full bg-${dim.color}`} style={{ width: `${dim.score}%` }}></div>
                                                     </div>
                                                 </div>
                                             ))}
                                         </div>
                                     </div>
                                     <div className="p-5 bg-white/[0.03] border border-white/10 rounded-2xl relative overflow-hidden">
                                         <div className="absolute top-0 right-0 p-3 opacity-10"><Target className="w-12 h-12 text-primary" /></div>
                                         <p className="text-[10px] font-black text-primary-light uppercase tracking-widest mb-4">Roadmap to 100</p>
                                         <div className="space-y-3">
                                             {[
                                                 { task: "Optimize COMPUTE_WH scaling policy", done: false },
                                                 { task: "Archive 12.5GB of stale storage", done: false },
                                                 { task: "Rotate long-running ETL queries", done: true },
                                             ].map((item, i) => (
                                                 <div key={i} className="flex items-center gap-3">
                                                     <div className={`w-4 h-4 rounded border flex items-center justify-center ${item.done ? 'bg-success border-success' : 'border-white/20'}`}>
                                                         {item.done && <CheckCircle className="w-3 h-3 text-white" />}
                                                     </div>
                                                     <span className={`text-[11px] font-medium ${item.done ? 'text-text-muted line-through' : 'text-white'}`}>{item.task}</span>
                                                 </div>
                                             ))}
                                         </div>
                                     </div>
                                 </div>
                            </motion.div>
                        )}

                        {selectedTab === 'spend' && (
                            <motion.div key="spend" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                <div className="flex items-center justify-between mb-8">
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1">Credit Utilization Details</h3>
                                        <p className="text-xs text-text-muted">Analyzing the historical 30-day trend for your account compute spend.</p>
                                    </div>
                                </div>
                                <div className="h-[200px]">
                                    {chartData.length > 0 ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={chartData}>
                                                <defs>
                                                    <linearGradient id="colorCredits" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                                                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f2937" />
                                                <XAxis dataKey="name" stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                                                <YAxis stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                                                <Tooltip contentStyle={{ backgroundColor: '#0d1829', border: '1px solid #1a2e4a', borderRadius: '12px' }} />
                                                <Area type="monotone" dataKey="credits" stroke="#2563eb" strokeWidth={3} fill="url(#colorCredits)" />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center h-full border border-dashed border-white/10 rounded-2xl bg-white/[0.02]">
                                            <TrendingUp className="w-8 h-8 text-text-muted/20 mb-3" />
                                            <p className="text-xs font-bold text-text-muted uppercase tracking-widest">No historical spend data yet</p>
                                            <p className="text-[10px] text-text-muted/60 mt-1">Activity will appear here as Snowflake updates its usage logs.</p>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                        
                        {selectedTab === 'savings' && (
                            <motion.div key="savings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                                <h3 className="text-xl font-bold text-white">Savings Opportunities</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    {(savings?.recommendations || savings?.items || []).slice(0, 4).map((rec, i) => (
                                        <div key={i} className="p-4 bg-white/5 border border-white/10 rounded-xl">
                                            <div className="flex items-center gap-2 mb-2">
                                                <div className={`p-1.5 rounded-lg bg-${rec.severity === 'HIGH' ? 'danger' : 'primary'}/10`}>
                                                    <Zap className={`w-4 h-4 text-${rec.severity === 'HIGH' ? 'danger' : 'primary'}`} />
                                                </div>
                                                <span className="text-xs font-bold text-white">{rec.title}</span>
                                            </div>
                                            <p className="text-[10px] text-text-muted leading-relaxed line-clamp-2">{rec.detail}</p>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {selectedTab === 'alerts' && (
                            <motion.div key="alerts" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                                <h3 className="text-xl font-bold text-white">Critical Performance Alerts</h3>
                                <div className="space-y-3">
                                    {session?.anomaly?.recent_anomalies?.length > 0 ? (
                                        session.anomaly.recent_anomalies.slice(0, 3).map((alert, i) => (
                                            <div key={i} className="flex items-center justify-between p-4 bg-white/[0.02] border border-border rounded-xl group hover:border-danger/30 transition-all">
                                                <div className="flex items-center gap-4">
                                                    <div className="p-2 bg-danger/10 border border-danger/20 rounded-lg">
                                                        <AlertCircle className="w-5 h-5 text-danger" />
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-bold text-white">{alert.warehouse}</span>
                                                        <span className="text-[10px] text-text-muted italic">{alert.description}</span>
                                                    </div>
                                                </div>
                                                <div className="text-right flex items-center gap-4">
                                                    <div>
                                                        <p className="text-[9px] font-black text-danger uppercase mb-0.5">Anomaly</p>
                                                        <p className="text-xs font-black text-white">+{alert.magnitude?.toFixed(0)}% Credit Spike</p>
                                                    </div>
                                                    <button className="p-2 bg-sidebar border border-border rounded-lg hover:text-danger-light group-hover:bg-danger/10 transition-all">
                                                        <ArrowRight className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="p-10 border border-dashed border-border rounded-xl text-center">
                                            <p className="text-xs text-text-muted font-bold uppercase tracking-widest">No active anomalies detected</p>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                <div className="glass-card p-8 flex flex-col">
                    <div className="mb-6">
                      <h3 className="text-lg font-bold text-white mb-1">AI Recommendation</h3>
                      <p className="text-xs text-text-muted font-medium">Real-time insight from session data</p>
                    </div>
                    
                    <div className="flex-1 flex flex-col justify-start items-center text-center p-6 bg-primary/5 border border-dashed border-primary/20 rounded-2xl min-h-[300px]">
                        <div className="p-3 bg-primary/20 rounded-full mb-4 shrink-0">
                            <Sparkles className="w-6 h-6 text-primary-light" />
                        </div>
                        <div className="text-sm font-medium text-white leading-relaxed mb-6 text-left w-full h-full max-h-[400px] overflow-y-auto whitespace-pre-wrap">
                            {isGenerating ? <span className="animate-pulse text-primary-light">Generating real-time SQL architecture strategy via Groq API...</span> : aiRecs}
                        </div>
                        <button 
                            onClick={handleExecuteAdvice}
                            disabled={isGenerating}
                            className={`px-8 py-3 w-full bg-primary text-white text-xs font-bold rounded-xl transition-all mt-auto ${isGenerating ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary-dark'}`}
                        >
                            {isGenerating ? 'Analyzing...' : 'Execute Advice'}
                        </button>
                    </div>
                    
                    <div className="mt-8 pt-8 border-t border-border">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Dimension Health</span>
                        </div>
                        <div className="space-y-4">
                            {[
                                { name: 'Query Perf', score: health?.scores?.query || 0, icon: Target },
                                { name: 'Warehouse', score: health?.scores?.warehouse || 0, icon: Layers },
                                { name: 'Storage', score: health?.scores?.storage || 0, icon: Archive },
                            ].map((dim) => (
                                <div key={dim.name} className="flex items-center gap-3">
                                    <dim.icon className="w-3.5 h-3.5 text-text-muted" />
                                    <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                                        <div className={`h-full bg-${dim.score >= 75 ? 'success' : dim.score >= 50 ? 'warning' : 'danger'}`} style={{ width: `${dim.score}%` }}></div>
                                    </div>
                                    <span className="text-[10px] font-bold text-white min-w-[24px]">{dim.score}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default Overview;
