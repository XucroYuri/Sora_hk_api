
import React, { useState, useEffect } from 'react';
import { Run } from '../../types';
import { api } from '../../services/api';
import { useI18n } from '../../App';
import { Button, Card, StatusBadge } from '../../components/ui';

export const RunList: React.FC = () => {
  const { t } = useI18n();
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  // Auto-refresh hook
  useEffect(() => {
    const fetch = async () => {
      const data = await api.getRuns();
      setRuns(data);
      setLoading(false);
    };
    fetch();
    const interval = setInterval(fetch, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800">{t('nav.runs')}</h2>
        <Button onClick={() => window.location.hash = '#/runs/create'}>
          + {t('action.create_run')}
        </Button>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-100 uppercase text-xs font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-4">{t('col.id')}</th>
                <th className="px-6 py-4">{t('nav.storyboards')}</th>
                <th className="px-6 py-4">{t('col.status')}</th>
                <th className="px-6 py-4">{t('col.progress')}</th>
                <th className="px-6 py-4">{t('col.tasks')}</th>
                <th className="px-6 py-4 text-right">{t('col.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                 <tr><td colSpan={6} className="px-6 py-8 text-center">{t('state.loading')}</td></tr>
              ) : runs.map((run) => (
                <tr key={run.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs">{run.id}</td>
                  <td className="px-6 py-4 font-medium">{run.storyboard_name || run.storyboard_id || run.id}</td>
                  <td className="px-6 py-4"><StatusBadge status={run.status} label={t(`status.${run.status}` as any)} /></td>
                  <td className="px-6 py-4">
                     <div className="flex items-center gap-2">
                       <div className="w-24 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                         <div className="bg-blue-600 h-1.5" style={{ width: `${run.total_tasks ? (run.completed / run.total_tasks) * 100 : 0}%` }}></div>
                       </div>
                       <span className="text-xs text-slate-500">{run.total_tasks ? Math.round((run.completed / run.total_tasks) * 100) : 0}%</span>
                     </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-xs">
                       <span className="text-green-600 font-medium">{run.completed}</span> / 
                       <span className="text-red-500 font-medium ml-1">{run.failed}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <a href={`#/runs/${run.id}`} className="text-blue-600 hover:text-blue-800 font-medium">{t('action.view')}</a>
                  </td>
                </tr>
              ))}
              {!loading && runs.length === 0 && (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-400">{t('state.empty')}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
