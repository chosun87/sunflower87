import React, { useState } from 'react';
import Sidebar from '@components/Sidebar';
import Header from '@components/Header';
import { ConfirmDialog } from '@/assets/ts/PrimeReact';

interface LayoutProps {
  children: React.ReactNode;
  isDarkMode: boolean;
  toggleTheme: () => void;
}

export default function Layout({ children, isDarkMode, toggleTheme }: LayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <div className="app-layout">
      <Sidebar collapsed={sidebarCollapsed} />
      <div className="main-wrapper">
        <Header isDarkMode={isDarkMode} toggleTheme={toggleTheme} toggleSidebar={toggleSidebar} />
        {children}
      </div>

      <ConfirmDialog />
    </div>
  );
}
