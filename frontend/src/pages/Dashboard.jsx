import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate, Routes, Route } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import Overview from './Overview';
import Warehouse from './Warehouse';
import QueryIntelligence from './QueryIntelligence';
import SpendAnomaly from './SpendAnomaly';
import CostBreakdown from './CostBreakdown';
import StorageAnalytics from './StorageAnalytics';
import UnusedObjects from './UnusedObjects';
import CloudServices from './CloudServices';
import Notebooks from './Notebooks';
import { motion, AnimatePresence } from 'framer-motion';

const Dashboard = () => {
    const { session } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    if (!session) {
        return <Navigate to="/login" />;
    }

    return (
        <div className="flex min-h-screen bg-background relative selection:bg-primary/40 selection:text-text">
            {/* Background Grain */}
            <div className="fixed inset-0 opacity-[0.03] pointer-events-none z-[100] bg-[url('https://grainy-gradients.vercel.app/noise.svg')]"></div>
            
            <Sidebar />
            
            <main className="flex-1 ml-72 flex flex-col relative">
                <TopBar />
                
                <div className="flex-1 p-10 overflow-x-hidden">
                   <div className="max-w-[1600px] mx-auto">
                    <AnimatePresence mode="wait">
                        <Routes>
                            <Route index element={<Overview />} />
                            <Route path="warehouse" element={<Warehouse />} />
                            <Route path="queries" element={<QueryIntelligence />} />
                            <Route path="anomaly" element={<SpendAnomaly />} />
                            <Route path="cost" element={<CostBreakdown />} />
                            <Route path="storage" element={<StorageAnalytics />} />
                            <Route path="unused" element={<UnusedObjects />} />
                            <Route path="cloud" element={<CloudServices />} />
                            <Route path="notebooks" element={<Notebooks />} />
                        </Routes>
                    </AnimatePresence>
                   </div>
                </div>
                
                <footer className="p-8 border-t border-border mt-10">
                   <div className="flex justify-between items-center text-[11px] font-bold text-text-muted uppercase tracking-widest px-2">
                       <p className="">&copy; 2026 SnowAdvisor Platform</p>
                       <div className="flex gap-6">
                           <a href="#" className="hover:text-primary transition-colors">Documentation</a>
                           <a href="#" className="hover:text-primary transition-colors">Support</a>
                           <a href="#" className="hover:text-primary transition-colors">API Reference</a>
                       </div>
                   </div>
                </footer>
            </main>
        </div>
    );
};

export default Dashboard;
