import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Database, 
  BarChart3, 
  AlertTriangle, 
  Layers, 
  Archive, 
  BookOpen, 
  Cloud,
  TrendingDown,
  LogOut,
  Snowflake,
  Shield
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
    const { logout } = useAuth();

    const menuItems = [
        { name: 'Warehouse', icon: Database, path: '/dashboard/warehouse' },
        { name: 'Query Intelligence', icon: Search, path: '/dashboard/queries' },
        { name: 'Spend Anomaly', icon: AlertTriangle, path: '/dashboard/anomaly' },
        { name: 'Cost Breakdown', icon: BarChart3, path: '/dashboard/cost' },
        { name: 'Storage', icon: Archive, path: '/dashboard/storage' },
        { name: 'Notebooks', icon: BookOpen, path: '/dashboard/notebooks' },
    ];

    return (
        <aside className="fixed left-0 top-0 h-screen w-72 bg-[#2C7DA0]/90 backdrop-blur-2xl border-r border-white/20 z-50 flex flex-col pt-8">
            <div className="px-8 mb-10">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/10 border border-white/20 rounded-xl">
                        <Snowflake className="w-6 h-6 text-[#38BDF8]" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold tracking-tight text-white leading-none">Snow<span className="text-[#0284C7]">Advisor</span></h2>
                        <span className="text-[10px] text-white/40 font-bold uppercase tracking-widest mt-1 inline-block">Cost Control</span>
                    </div>
                </div>
            </div>

            <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto">
                <NavLink 
                    to="/dashboard" 
                    end
                    className={({ isActive }) => isActive ? 'side-nav-item-active' : 'side-nav-item'}
                >
                    <LayoutDashboard className="w-5 h-5 mr-3 flex-shrink-0" />
                    Overview
                </NavLink>

                <div className="h-4 pl-4 pt-4 mb-2">
                    <span className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Optimization</span>
                </div>

                {menuItems.map((item) => (
                    <NavLink 
                        key={item.name} 
                        to={item.path} 
                        className={({ isActive }) => isActive ? 'side-nav-item-active' : 'side-nav-item'}
                    >
                        <item.icon className="w-5 h-5 mr-3 flex-shrink-0" />
                        {item.name}
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 border-t border-border mt-auto">
                <button 
                    onClick={logout}
                    className="w-full side-nav-item text-danger hover:bg-danger/5 transition-colors"
                >
                    <LogOut className="w-5 h-5 mr-3" />
                    Sign Out
                </button>
            </div>
        </aside>
    );
};

const Search = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="11" cy="11" r="8" />
    <path d="m21 21-4.3-4.3" />
  </svg>
);

export default Sidebar;
