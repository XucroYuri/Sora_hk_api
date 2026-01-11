
import React from 'react';
import { useI18n } from '../App';

const SidebarItem: React.FC<{ 
  href: string; 
  label: string; 
  icon: React.ReactNode; 
  active?: boolean 
}> = ({ href, label, icon, active }) => (
  <a 
    href={href} 
    className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
      active 
        ? 'bg-blue-50 text-blue-700' 
        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
    }`}
  >
    <span className="w-5 h-5">{icon}</span>
    {label}
  </a>
);

const MobileNavItem: React.FC<{ 
  href: string; 
  label: string; 
  icon: React.ReactNode; 
  active?: boolean 
}> = ({ href, label, icon, active }) => (
  <a 
    href={href} 
    className={`flex flex-col items-center justify-center w-full py-2 transition-colors ${
      active 
        ? 'text-blue-600' 
        : 'text-slate-500 hover:text-slate-900'
    }`}
  >
    <span className="w-6 h-6">{icon}</span>
    <span className="text-[10px] font-medium mt-1">{label}</span>
  </a>
);

interface LayoutProps {
  children: React.ReactNode;
  currentPath: string;
}

export const Layout: React.FC<LayoutProps> = ({ children, currentPath }) => {
  const { t, locale, setLocale } = useI18n();
  const path = currentPath || '#/dashboard';

  const icons = {
    dashboard: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>,
    storyboards: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>,
    runs: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
    results: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg>,
    settings: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar (Desktop) */}
      <aside className="w-64 bg-white border-r border-slate-200 fixed h-full hidden md:flex flex-col z-10">
        <div className="h-16 flex items-center px-6 border-b border-slate-100">
          <div className="flex items-center gap-2 text-blue-600 font-bold text-xl tracking-tight">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zm0 9l2.5-1.25L12 8.5l-2.5 1.25L12 11zm0 2.5l-5-2.5-5 2.5L12 22l10-8.5-5-2.5-5 2.5z"/></svg>
            CineFlow
          </div>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto no-scrollbar">
          <SidebarItem 
            href="#/dashboard" 
            label={t('nav.dashboard')} 
            active={path === '#/dashboard' || path === ''}
            icon={icons.dashboard} 
          />
          <SidebarItem 
            href="#/storyboards" 
            label={t('nav.storyboards')} 
            active={path.startsWith('#/storyboards')}
            icon={icons.storyboards} 
          />
          <SidebarItem 
            href="#/runs" 
            label={t('nav.runs')} 
            active={path.startsWith('#/runs')}
            icon={icons.runs} 
          />
          <SidebarItem 
            href="#/results" 
            label={t('nav.results')} 
            active={path.startsWith('#/results')}
            icon={icons.results} 
          />
           <div className="pt-4 mt-4 border-t border-slate-100">
             <SidebarItem 
              href="#/settings" 
              label={t('nav.settings')} 
              active={path.startsWith('#/settings')}
              icon={icons.settings} 
            />
           </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 md:ml-64 flex flex-col min-h-screen pb-20 md:pb-0">
        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-20 px-6 flex items-center justify-between">
          <h1 className="font-semibold text-lg text-slate-800">{t('app.title')}</h1>
          <div className="flex items-center gap-4">
             <select 
              className="text-sm bg-slate-50 border-none rounded-md py-1 px-2 focus:ring-2 focus:ring-blue-500 cursor-pointer"
              value={locale}
              onChange={(e) => setLocale(e.target.value as any)}
             >
               <option value="zh-CN">🇨🇳 中文</option>
               <option value="en-US">🇺🇸 English</option>
             </select>
             <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-sm">
               D
             </div>
          </div>
        </header>

        {/* Content Body */}
        <div className="p-6 md:p-8 max-w-7xl mx-auto w-full">
           {children}
        </div>
      </main>

      {/* Bottom Nav (Mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 h-16 flex items-center justify-around z-30 px-2 shadow-[0_-1px_3px_rgba(0,0,0,0.05)]">
        <MobileNavItem 
          href="#/dashboard" 
          label={t('nav.dashboard')} 
          active={path === '#/dashboard' || path === ''}
          icon={icons.dashboard} 
        />
        <MobileNavItem 
          href="#/storyboards" 
          label={t('nav.storyboards')} 
          active={path.startsWith('#/storyboards')}
          icon={icons.storyboards} 
        />
        <MobileNavItem 
          href="#/runs" 
          label={t('nav.runs')} 
          active={path.startsWith('#/runs')}
          icon={icons.runs} 
        />
        <MobileNavItem 
          href="#/results" 
          label={t('nav.results')} 
          active={path.startsWith('#/results')}
          icon={icons.results} 
        />
        <MobileNavItem 
          href="#/settings" 
          label={t('nav.settings')} 
          active={path.startsWith('#/settings')}
          icon={icons.settings} 
        />
      </nav>
    </div>
  );
};
