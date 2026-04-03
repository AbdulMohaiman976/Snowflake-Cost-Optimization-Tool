import React from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Bell, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';

const TopBar = () => {
    const { session } = useAuth();
    const info = session?.account_info || {};

    return (
        <header className="h-20 border-b border-border bg-sidebar px-10 flex items-center justify-between sticky top-0 z-40 backdrop-blur-xl bg-opacity-70">
            <div className="flex items-center gap-4">
                <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                    <User className="w-5 h-5 text-primary-light" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white tracking-wide uppercase">Snowflake Context</h3>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-text-muted font-mono">{info.account}</span>
                    <span className="w-1 h-1 bg-white/20 rounded-full"></span>
                    <span className="text-xs text-text-muted">{info.user}</span>
                    <span className="w-1 h-1 bg-white/20 rounded-full"></span>
                    <span className="text-xs text-text-muted px-1.5 py-0.5 bg-primary/10 border border-primary/20 rounded text-primary-light font-bold text-[10px]">{info.role}</span>
                  </div>
                </div>
            </div>

            <div className="flex items-center gap-6">
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-sidebar rounded-lg border border-border">
                  <div className="w-2 h-2 bg-success rounded-full animate-pulse"></div>
                  <span className="text-[10px] font-bold text-success uppercase tracking-wider">Live Analysis</span>
                </div>
                
                <button className="p-2.5 text-text-muted hover:text-white transition-colors relative">
                  <Bell className="w-5 h-5" />
                  <span className="absolute top-2 right-2 w-2 h-2 bg-danger rounded-full border-2 border-sidebar"></span>
                </button>

                <div className="flex items-center gap-3 pl-6 border-l border-border h-10 group cursor-pointer">
                  <div className="text-right">
                    <p className="text-sm font-bold text-white group-hover:text-primary transition-colors">{info.user?.split('.')[0] || 'User'}</p>
                    <p className="text-[10px] text-text-muted font-bold tracking-widest uppercase">Member</p>
                  </div>
                  <div className="w-9 h-9 rounded-full bg-primary/20 border border-primary/20 flex items-center justify-center text-primary-light font-bold text-sm">
                    {info.user?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <ChevronDown className="w-4 h-4 text-text-muted" />
                </div>
            </div>
        </header>
    );
};

export default TopBar;
