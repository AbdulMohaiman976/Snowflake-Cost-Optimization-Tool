import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { generateAgentPlan } from '../api/api';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  Users, 
  Lock, 
  Key, 
  UserX,
  Search,
  Sparkles,
  ChevronRight,
  X,
  Terminal,
  ExternalLink,
  Copy,
  CheckCircle2
} from 'lucide-react';

const UserSecurity = () => {
    const { session } = useAuth();
    const securityData = session?.users || {};
    const users = securityData.users || [];
    const recommendations = securityData.recommendations || [];
    const securityEvents = securityData.security_events || [];

    const [selectedAlert, setSelectedAlert] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [copied, setCopied] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);
    const [agentPlan, setAgentPlan] = useState('');

    const handleApplySolution = async (alert) => {
        setSelectedAlert(alert);
        setIsModalOpen(true);
        setAgentPlan('');
        if (!alert.fix_sql) {
            setIsGenerating(true);
            try {
                const res = await generateAgentPlan(session?.session_id, 'users');
                setAgentPlan(res.plan);
            } catch (err) {
                setAgentPlan('-- LLM API Error: Failed to generate prescriptive SQL steps.');
            } finally {
                setIsGenerating(false);
            }
        }
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const filteredUsers = users.filter(u => 
        u.username.toLowerCase().includes(searchTerm.toLowerCase()) || 
        (u.role && u.role.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-8"
        >
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-text mb-2">User Security</h1>
                  <p className="text-text-muted text-sm max-w-lg leading-relaxed">Identity and access management analysis, detecting missing MFA, inactive accounts, and suspicious login activity.</p>
                </div>
                <div className="flex gap-4">
                  <div className="p-4 bg-black/30 border border-border rounded-xl">
                    <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 leading-none">Security Score</p>
                    <div className="flex items-center gap-2">
                        <ShieldCheck className={`w-5 h-5 ${securityData.score >= 80 ? 'text-success' : securityData.score >= 50 ? 'text-warning' : 'text-danger'}`} />
                        <p className="text-xl font-black text-text font-mono">{securityData.score || 0}/100</p>
                    </div>
                  </div>
                </div>
            </div>

            <div className="grid grid-cols-4 gap-6">
                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44 border-b-4 border-danger">
                    <div>
                        <div className="p-2 bg-danger/10 border border-danger/20 rounded-lg w-fit mb-4">
                            <Lock className="w-5 h-5 text-danger" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1 leading-none">Admins Missing MFA</p>
                        <h4 className="text-2xl font-extrabold text-text">{securityData.admin_no_mfa || 0}</h4>
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44 border-b-4 border-warning">
                    <div>
                        <div className="p-2 bg-warning/10 border border-warning/20 rounded-lg w-fit mb-4">
                            <Key className="w-5 h-5 text-warning" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1 leading-none">Total Missing MFA</p>
                        <h4 className="text-2xl font-extrabold text-text">{securityData.no_mfa_count || 0}</h4>
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-primary/10 border border-primary/20 rounded-lg w-fit mb-4">
                            <UserX className="w-5 h-5 text-primary" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1 leading-none">Inactive &gt; 90 Days</p>
                        <h4 className="text-2xl font-extrabold text-text">{securityData.inactive_count || 0}</h4>
                    </div>
                </div>

                <div className="p-6 glass-card bg-gradient-to-br from-sidebar/80 to-background flex flex-col justify-between h-44">
                    <div>
                        <div className="p-2 bg-danger/10 border border-danger/20 rounded-lg w-fit mb-4">
                            <ShieldAlert className="w-5 h-5 text-danger-light" />
                        </div>
                        <p className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em] mb-1 leading-none">Failed Logins (30d)</p>
                        <h4 className="text-2xl font-extrabold text-text">{securityData.failed_logins || 0}</h4>
                    </div>
                </div>
            </div>

            {securityEvents.length > 0 && (
                <div className="glass-card p-6 border border-danger/30 bg-danger/5">
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-danger" /> Critical Security Events
                    </h3>
                    <div className="space-y-3">
                        {securityEvents.map((evt, idx) => (
                            <div key={idx} className="flex items-start gap-4 p-4 bg-black/30 rounded-lg border border-danger/20">
                                <div className="mt-0.5 w-2 h-2 rounded-full bg-danger"></div>
                                <div>
                                    <p className="text-sm font-bold text-text">{evt.event} <span className="text-text-muted text-xs font-normal">({evt.date})</span></p>
                                    <p className="text-xs text-text-muted mt-1">{evt.detail} — User: <span className="text-text font-mono">{evt.user}</span></p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 gap-6">
                <div className="glass-card p-6 bg-primary/5 border border-primary/20">
                    <div className="flex items-center gap-2 mb-4">
                        <Sparkles className="w-5 h-5 text-primary" />
                        <h3 className="text-sm font-bold text-text uppercase tracking-widest">Actionable Intelligence</h3>
                    </div>
                    {recommendations.length > 0 ? (
                        <div className="grid grid-cols-2 gap-6">
                            {recommendations.map((alert, i) => (
                                <div key={i} className="p-4 bg-sidebar/40 border border-border rounded-xl flex flex-col justify-between hover:border-primary/30 transition-colors">
                                    <div>
                                        <div className={`text-[9px] font-black uppercase mb-2 ${alert.severity === 'HIGH' ? 'text-danger' : alert.severity === 'MEDIUM' ? 'text-warning' : 'text-success'}`}>
                                            {alert.severity} PRIORITY
                                        </div>
                                        <p className="text-sm font-bold text-text mb-2">{alert.title}</p>
                                        <div className="p-3 bg-background/50 rounded-lg mb-4 border-l-2 border-primary">
                                            <p className="text-[10px] text-primary font-black mb-1 uppercase">Analysis:</p>
                                            <p className="text-[11px] text-text-muted leading-relaxed italic">{alert.detail}</p>
                                        </div>
                                    </div>
                                    <button 
                                        onClick={() => handleApplySolution(alert)}
                                        className="mt-2 text-[10px] font-black text-primary uppercase tracking-widest hover:text-text transition-colors flex items-center gap-1 group w-fit"
                                    >
                                        Apply Fix <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="p-6 text-center text-text-muted text-sm font-medium">
                            No active security alerts. Your environment looks secure.
                        </div>
                    )}
                </div>
            </div>

            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-border bg-sidebar/30 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-text uppercase tracking-widest">User Registry</h3>
                  <div className="flex gap-2 relative">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
                    <input 
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="bg-sidebar-item border border-border rounded-lg py-1.5 pl-8 pr-3 text-[11px] text-text focus:outline-none focus:border-primary/50 transition-all w-[240px]" 
                        placeholder="Search username or role..." 
                    />
                  </div>
                </div>
                
                <div className="overflow-x-auto max-h-[400px]">
                    <table className="w-full text-left border-collapse table-fixed">
                        <thead className="sticky top-0 z-10 bg-sidebar">
                            <tr className="bg-black/30 text-[10px] font-bold text-text-muted uppercase tracking-widest border-b border-border">
                                <th className="px-4 py-4 w-[25%]">Username</th>
                                <th className="px-4 py-4 w-[20%]">Role</th>
                                <th className="px-4 py-4 w-[15%] text-center">Status</th>
                                <th className="px-4 py-4 w-[15%] text-center">MFA</th>
                                <th className="px-4 py-4 w-[25%]">Last Login</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                            {filteredUsers.length > 0 ? filteredUsers.map((u, idx) => (
                                <tr key={idx} className="group hover:bg-black/[0.02] transition-colors">
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <div className="w-6 h-6 rounded bg-sidebar border border-border flex items-center justify-center">
                                                <Users className="w-3 h-3 text-text-muted" />
                                            </div>
                                            <span className="text-xs font-bold text-text truncate max-w-[150px]" title={u.username}>{u.username}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-[10px] font-mono text-text-muted truncate">
                                        {u.role || 'N/A'}
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        {u.disabled ? (
                                            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-sidebar text-text-muted border border-border">Disabled</span>
                                        ) : u.days_inactive > 90 ? (
                                            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-warning/10 text-warning border border-warning/20">Inactive</span>
                                        ) : (
                                            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-success/10 text-success border border-success/20">Active</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        {u.has_mfa ? (
                                            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-success/10 text-success border border-success/20">Enabled</span>
                                        ) : (
                                            <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${u.role?.toUpperCase().includes('ADMIN') ? 'bg-danger/10 text-danger border border-danger/20' : 'bg-warning/10 text-warning border border-warning/20'}`}>Disabled</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-[10px] text-text-muted">
                                        {u.last_login} <span className="opacity-50">({u.days_inactive} days ago)</span>
                                    </td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan="5" className="px-4 py-8 text-center text-text-muted text-xs">
                                        No users found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
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
                                        <p className="text-xs text-text-muted">Security Policy Fix</p>
                                    </div>
                                </div>
                                <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-black/5 rounded-lg text-text-muted transition-colors">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="p-8 space-y-6">
                                <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 p-1.5 px-3 bg-primary/10 text-[9px] font-black text-primary uppercase tracking-[0.2em] rounded-bl-xl border-l border-b border-primary/20">SECURITY INSIGHT</div>
                                    <div className="flex items-start gap-4">
                                        <div className="mt-1 p-2 bg-primary/10 rounded-lg text-primary">
                                            <ShieldAlert className="w-4 h-4" />
                                        </div>
                                        <div>
                                            <h4 className="text-[10px] font-black text-text/40 uppercase tracking-[0.15em] mb-1">Observation</h4>
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
                                        {selectedAlert.fix_sql && (
                                            <button 
                                                onClick={() => copyToClipboard(selectedAlert.fix_sql)}
                                                className="flex items-center gap-2 text-[10px] font-bold text-text-muted hover:text-text transition-colors py-1 px-2 rounded-lg hover:bg-black/5"
                                            >
                                                {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                                                {copied ? 'COPIED' : 'COPY COMMANDS'}
                                            </button>
                                        )}
                                    </div>
                                    <div className="relative group">
                                        <div className="absolute inset-0 bg-primary/5 rounded-xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                                        <pre className="relative p-6 bg-background/50 border border-border rounded-xl font-mono text-xs text-text-accent leading-relaxed overflow-x-auto min-h-[120px]">
                                            {isGenerating ? (
                                                <span className="animate-pulse text-primary">Generating real-time SQL security fix via Groq API...</span>
                                            ) : (
                                                <code>{selectedAlert.fix_sql || agentPlan || '-- Follow UI instructions mentioned in the observation.'}</code>
                                            )}
                                        </pre>
                                    </div>
                                </div>

                                <div className="pt-4 flex items-center gap-4">
                                    <button 
                                        onClick={() => setIsModalOpen(false)}
                                        className="flex-1 py-3 px-4 bg-primary text-background font-black text-xs uppercase tracking-widest rounded-xl hover:bg-primary-light transition-colors flex items-center justify-center gap-2"
                                    >
                                        <ExternalLink className="w-4 h-4" /> Go to Snowflake
                                    </button>
                                    <button 
                                        onClick={() => setIsModalOpen(false)}
                                        className="px-6 py-3 border border-border text-text font-black text-xs uppercase tracking-widest rounded-xl hover:bg-black/5 transition-colors"
                                    >
                                        Close
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

export default UserSecurity;
