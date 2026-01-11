
import React, { useState, useEffect } from 'react';
import { useI18n } from '../../App';
import { Card, StatusBadge } from '../../components/ui';
import { api } from '../../services/api';
import { Run, RunStatus } from '../../types';

export const Dashboard: React.FC = () => {
  const { t } = useI18n();
  const [runs, setRuns] = useState<Run[]>([]);
  const [stats, setStats] = useState({ active: 0, total: 0, successRate: 0 });

  useEffect(() => {
    const fetchStats = async () => {
      const data = await api.getRuns();
      setRuns(data);

      const total = data.length;
      const active = data.filter(r => r.status === RunStatus.Running || r.status === RunStatus.Queued).length;
      const completed = data.filter(r => r.status === RunStatus.Completed);
      // Simple success rate based on completed runs vs total (excluding active for accuracy, or just raw)
      // Here: (Completed Runs / Total Runs that aren't active) * 100
      const finishedRuns = data.filter(r => r.status !== RunStatus.Running && r.status !== RunStatus.Queued).length;
      const rate = finishedRuns > 0 ? (completed.length / finishedRuns) * 100 : 0;

      setStats({
        active,
        total,
        successRate: Math.round(rate)
      });
    };
    fetchStats();
  }, []);

  const StatCard = ({ title, value, icon, color }: any) => (
    <Card className="flex items-center p-6 gap-4">
      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-slate-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
      </div>
    </Card>
  );

  return (
    <div className="space-y-8">
      <div>
         <h2 className="text-2xl font-bold text-slate-800 mb-2">{t('nav.dashboard')}</h2>
         <p className="text-slate-500">{t('dash.welcome')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title={t('dash.active_tasks')} 
          value={stats.active} 
          color="bg-blue-100 text-blue-600"
          icon={<svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
        />
        <StatCard 
          title={t('dash.total_runs')} 
          value={stats.total} 
          color="bg-purple-100 text-purple-600"
          icon={<svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>}
        />
        <StatCard 
          title={t('dash.success_rate')} 
          value={`${stats.successRate}%`} 
          color="bg-green-100 text-green-600"
          icon={<svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
      </div>

      <Card title={t('dash.recent_runs')}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
             <thead className="bg-slate-50 border-b border-slate-100 uppercase text-xs font-semibold text-slate-500">
               <tr>
                 <th className="px-6 py-3">{t('col.name')}</th>
                 <th className="px-6 py-3">{t('col.status')}</th>
                 <th className="px-6 py-3">{t('col.progress')}</th>
                 <th className="px-6 py-3 text-right">{t('col.actions')}</th>
               </tr>
             </thead>
             <tbody className="divide-y divide-slate-100">
                {runs.slice(0, 5).map(run => (
                  <tr key={run.id} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-medium text-slate-900">{run.storyboard_name || run.id}</td>
                    <td className="px-6 py-3"><StatusBadge status={run.status} label={t(`status.${run.status}` as any)} /></td>
                    <td className="px-6 py-3">
                       <div className="w-24 bg-slate-200 rounded-full h-1.5">
                         <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${(run.completed / run.total_tasks) * 100}%` }}></div>
                       </div>
                    </td>
                    <td className="px-6 py-3 text-right">
                       <a href={`#/runs/${run.id}`} className="text-blue-600 hover:underline">{t('action.view')}</a>
                    </td>
                  </tr>
                ))}
                {runs.length === 0 && (
                   <tr><td colSpan={4} className="px-6 py-8 text-center text-slate-400">{t('state.empty')}</td></tr>
                )}
             </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
