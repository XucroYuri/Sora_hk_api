

import React, { useState, useEffect } from 'react';
import { Model, Provider } from '../../types';
import { api } from '../../services/api';
import { useI18n } from '../../App';
import { Button, Card, Select, useToast } from '../../components/ui';

type Tab = 'general' | 'models' | 'providers';

export const SettingsPage: React.FC = () => {
  const { t, locale, setLocale } = useI18n();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('general');
  const [models, setModels] = useState<Model[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);

  useEffect(() => {
    if (activeTab === 'models') {
      api.getModels().then(setModels);
    } else if (activeTab === 'providers') {
      api.getProviders().then(setProviders);
    }
  }, [activeTab]);

  const handleToggleModel = async (id: string, currentStatus: boolean) => {
    try {
      await api.toggleModel(id, !currentStatus);
      setModels(prev => prev.map(m => m.id === id ? { ...m, enabled: !currentStatus } : m));
      showToast(t('msg.save_success'), 'success');
    } catch (e) {
      showToast(t('error.generic'), 'error');
    }
  };

  const handleToggleProvider = async (id: string, currentStatus: boolean) => {
    try {
      await api.toggleProvider(id, !currentStatus);
      setProviders(prev => prev.map(p => p.id === id ? { ...p, enabled: !currentStatus } : p));
      showToast(t('msg.save_success'), 'success');
    } catch (e) {
      showToast(t('error.generic'), 'error');
    }
  };

  const TabButton = ({ id, label }: { id: Tab, label: string }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
        activeTab === id 
          ? 'border-blue-600 text-blue-600' 
          : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="space-y-6 max-w-5xl">
      <h2 className="text-2xl font-bold text-slate-800">{t('title.settings')}</h2>

      <div className="flex border-b border-slate-200">
        <TabButton id="general" label={t('tab.general')} />
        <TabButton id="models" label={t('tab.models')} />
        <TabButton id="providers" label={t('tab.providers')} />
      </div>

      <div className="py-4">
        {/* General Tab */}
        {activeTab === 'general' && (
          <Card title={t('tab.general')}>
             <div className="max-w-md space-y-4">
                <Select 
                  label={t('label.language')}
                  value={locale}
                  onChange={(e) => {
                    setLocale(e.target.value as any);
                    showToast(t('msg.save_success'), 'success');
                  }}
                  options={[
                    { value: 'zh-CN', label: '简体中文 (Chinese)' },
                    { value: 'en-US', label: 'English (US)' },
                  ]}
                />
                <div className="text-xs text-slate-500 pt-4 border-t border-slate-100">
                   {t('label.system_version')}: v0.1.0-beta
                </div>
             </div>
          </Card>
        )}

        {/* Models Tab */}
        {activeTab === 'models' && (
          <Card title={t('tab.models')}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-100">
                   <tr>
                     <th className="px-4 py-3">{t('col.model_name')}</th>
                     <th className="px-4 py-3">{t('col.description')}</th>
                     <th className="px-4 py-3">{t('col.status')}</th>
                     <th className="px-4 py-3 text-right">{t('col.actions')}</th>
                   </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {models.map(model => (
                    <tr key={model.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-800">{model.display_name}</td>
                      <td className="px-4 py-3 text-slate-500">{model.description}</td>
                      <td className="px-4 py-3">
                         <span className={`px-2 py-0.5 rounded text-xs ${model.enabled ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                           {model.enabled ? t('status.active') : t('status.disabled')}
                         </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                         <Button 
                           size="sm" 
                           variant={model.enabled ? 'secondary' : 'primary'}
                           onClick={() => handleToggleModel(model.id, model.enabled)}
                         >
                           {model.enabled ? t('action.disable') : t('action.enable')}
                         </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Providers Tab */}
        {activeTab === 'providers' && (
          <Card title={t('tab.providers')}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-100">
                   <tr>
                     <th className="px-4 py-3">{t('label.provider')}</th>
                     <th className="px-4 py-3">{t('col.type')}</th>
                     <th className="px-4 py-3 text-center">{t('label.priority')}</th>
                     <th className="px-4 py-3 text-center">{t('label.weight')}</th>
                     <th className="px-4 py-3 text-right">{t('col.status')}</th>
                   </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {providers.map(provider => (
                    <tr key={provider.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-800">{provider.name}</td>
                      <td className="px-4 py-3 text-slate-500">{provider.type}</td>
                      <td className="px-4 py-3 text-center font-mono">{provider.priority}</td>
                      <td className="px-4 py-3 text-center font-mono">{provider.weight}</td>
                      <td className="px-4 py-3 text-right flex items-center justify-end gap-2">
                         <span className={`px-2 py-0.5 rounded text-xs ${provider.enabled ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'}`}>
                           {provider.enabled ? t('status.connected') : t('status.disconnected')}
                         </span>
                         <Button 
                           size="sm" 
                           variant="ghost"
                           onClick={() => handleToggleProvider(provider.id, provider.enabled)}
                         >
                           {provider.enabled ? t('action.disconnect') : t('action.connect')}
                         </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};
