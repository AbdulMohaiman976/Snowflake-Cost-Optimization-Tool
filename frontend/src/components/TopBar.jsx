import React from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Bell, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';

const TopBar = () => {
    const { session } = useAuth();
    const info = session?.account_info || {};

    return (
        <header className="h-20 border-b border-black/10 bg-white/60 px-10 flex items-center justify-between sticky top-0 z-40 backdrop-blur-xl">
            <div className="flex items-center gap-4">
                <div className="p-3 bg-white border border-black/10 rounded-xl">
                    <User className="w-5 h-5 text-[#2C7DA0]" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-black tracking-wide uppercase">Snowflake Context</h3>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-black/60 font-mono">{info.account}</span>
                    <span className="w-1 h-1 bg-black/20 rounded-full"></span>
                    <span className="text-xs text-black/60">{info.user}</span>
                    <span className="w-1 h-1 bg-black/20 rounded-full"></span>
                    <span className="text-xs text-[#2C7DA0] px-1.5 py-0.5 bg-white border border-black/10 rounded font-bold text-[10px]">{info.role}</span>
                  </div>
                </div>
            </div>

            <div className="flex items-center gap-6">
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white rounded-lg border border-black/10">
                  <div className="w-2 h-2 bg-[#2C7DA0] rounded-full animate-pulse"></div>
                  <span className="text-[10px] font-bold text-[#2C7DA0] uppercase tracking-wider">Live Analysis</span>
                </div>
                
                <button className="p-2.5 text-black/60 hover:text-black transition-colors relative">
                  <Bell className="w-5 h-5" />
                  <span className="absolute top-2 right-2 w-2 h-2 bg-[#2C7DA0] rounded-full border-2 border-white"></span>
                </button>

                <div className="flex items-center gap-3 pl-6 border-l border-black/10 h-10 group cursor-pointer">
                  <div className="text-right">
                    <p className="text-sm font-bold text-black group-hover:text-[#2C7DA0] transition-colors">{info.user?.split('.')[0] || 'User'}</p>
                    <p className="text-[10px] text-black/60 font-bold tracking-widest uppercase">Member</p>
                  </div>
                  <div className="w-9 h-9 rounded-full bg-white border border-black/10 flex items-center justify-center text-[#2C7DA0] font-bold text-sm">
                    {info.user?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <ChevronDown className="w-4 h-4 text-black/60" />
                </div>
            </div>
        </header>
    );
};

export default TopBar;
