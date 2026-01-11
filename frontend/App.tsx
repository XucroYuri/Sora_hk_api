
import React, { useState, useEffect, createContext, useContext } from 'react';
import { I18nContextType, Locale, I18nKeys } from './types';
import { RESOURCES } from './constants';
import { ToastProvider } from './components/ui';

// Components
import { Layout } from './components/layout';
import { Dashboard } from './features/dashboard/Dashboard';
import { StoryboardList } from './features/storyboards/StoryboardList';
import { StoryboardDetail } from './features/storyboards/StoryboardDetail';
import { RunList } from './features/runs/RunList';
import { RunCreate } from './features/runs/RunCreate';
import { RunDetail } from './features/runs/RunDetail';
import { ResultsList } from './features/results/ResultsList';
import { SettingsPage } from './features/settings/SettingsPage';

// --- Contexts ---
export const I18nContext = createContext<I18nContextType>({
  locale: 'zh-CN',
  setLocale: () => {},
  t: (key) => key,
});

export const useI18n = () => useContext(I18nContext);

// --- Simple Router ---
const useHashRouter = () => {
  const [hash, setHash] = useState(window.location.hash || '#/dashboard');
  
  useEffect(() => {
    const handleHashChange = () => setHash(window.location.hash || '#/dashboard');
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigate = (path: string) => {
    window.location.hash = path;
  };

  const getParams = (pattern: string) => {
    const hashParts = hash.replace('#', '').split('/');
    const patternParts = pattern.split('/');
    if (hashParts.length !== patternParts.length) return null;
    
    const params: Record<string, string> = {};
    for (let i = 0; i < patternParts.length; i++) {
      if (patternParts[i].startsWith(':')) {
        params[patternParts[i].substring(1)] = hashParts[i];
      } else if (patternParts[i] !== hashParts[i]) {
        return null;
      }
    }
    return params;
  };

  return { hash, navigate, getParams };
};

// --- App Component ---
export default function App() {
  const [locale, setLocale] = useState<Locale>('zh-CN');
  const { hash, getParams } = useHashRouter();

  const t = (key: I18nKeys, params?: Record<string, string | number>): string => {
    let str = RESOURCES[locale][key] || key;
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        str = str.replace(`{${k}}`, String(v));
      });
    }
    return str;
  };

  // Route Matching
  let content;
  const sbDetailParams = getParams('/storyboards/:id');
  const runDetailParams = getParams('/runs/:id');

  if (hash === '#/dashboard' || hash === '') {
    content = <Dashboard />;
  } else if (hash === '#/storyboards') {
    content = <StoryboardList />;
  } else if (sbDetailParams) {
    content = <StoryboardDetail id={sbDetailParams.id} />;
  } else if (hash === '#/runs') {
    content = <RunList />;
  } else if (hash === '#/runs/create') {
    content = <RunCreate />;
  } else if (runDetailParams) {
    content = <RunDetail id={runDetailParams.id} />;
  } else if (hash === '#/results') {
    content = <ResultsList />;
  } else if (hash === '#/settings') {
    content = <SettingsPage />;
  } else {
    content = <div className="p-8 text-center text-red-500">404 Not Found</div>;
  }

  return (
    <ToastProvider>
      <I18nContext.Provider value={{ locale, setLocale, t }}>
        <Layout currentPath={hash}>
          {content}
        </Layout>
      </I18nContext.Provider>
    </ToastProvider>
  );
}
