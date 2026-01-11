

import React, { useState, useEffect } from 'react';
import { Storyboard, Model, OutputMode, RunCreateRequest } from '../../types';
import { api } from '../../services/api';
import { useI18n } from '../../App';
import { Button, Card, Input, Select, useToast } from '../../components/ui';

export const RunCreate: React.FC = () => {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [storyboards, setStoryboards] = useState<Storyboard[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [formData, setFormData] = useState<RunCreateRequest>({
    storyboard_id: '',
    model_id: '',
    gen_count: 1,
    concurrency: 5,
    range: 'all',
    output_mode: OutputMode.Centralized,
    output_path: '',
    dry_run: false,
    force: false,
  });

  useEffect(() => {
    Promise.all([api.getStoryboards(), api.getModels()]).then(([sbData, modelData]) => {
       setStoryboards(sbData);
       setModels(modelData);
       if (sbData.length > 0) setFormData(prev => ({ ...prev, storyboard_id: sbData[0].id }));
       if (modelData.length > 0) setFormData(prev => ({ ...prev, model_id: modelData[0].id }));
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic Frontend Validation
    if (formData.output_mode === OutputMode.Custom && !formData.output_path) {
        showToast(t('error.schema_validation'), 'error');
        return;
    }

    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        range: formData.range.trim() ? formData.range.trim() : 'all',
        output_path: formData.output_mode === OutputMode.Custom ? formData.output_path : undefined,
      };
      await api.createRun(payload);
      showToast(t('msg.create_run_success'), 'success');
      window.location.hash = '#/runs';
    } catch (e) {
      showToast(t('error.generic'), 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4 mb-8">
        <a href="#/runs" className="text-slate-500 hover:text-blue-600">
           <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        </a>
        <h2 className="text-2xl font-bold text-slate-800">{t('action.create_run')}</h2>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <Select 
            label={t('nav.storyboards')}
            value={formData.storyboard_id}
            onChange={e => setFormData({...formData, storyboard_id: e.target.value})}
            options={storyboards.map(s => ({ value: s.id, label: s.name }))}
          />
          
          <Select 
            label={t('label.model')}
            value={formData.model_id}
            onChange={e => setFormData({...formData, model_id: e.target.value})}
            options={models.filter(m => m.enabled).map(m => ({ value: m.id, label: m.display_name }))}
          />

          <div className="grid grid-cols-2 gap-6">
            <Input 
              type="number" 
              label={t('label.count')}
              min={1} max={10}
              value={formData.gen_count}
              onChange={e => setFormData({...formData, gen_count: parseInt(e.target.value)})}
            />
            <Input 
              type="number" 
              label={t('label.concurrency')}
              min={1} max={50}
              value={formData.concurrency}
              onChange={e => setFormData({...formData, concurrency: parseInt(e.target.value)})}
            />
          </div>

          <Input 
            label={t('label.range')}
            placeholder={t('label.range_hint')}
            value={formData.range}
            onChange={e => setFormData({...formData, range: e.target.value})}
          />

          <div className="pt-2 border-t border-slate-100 mt-4">
             <label className="text-sm font-medium text-slate-700 mb-2 block">{t('label.exec_options')}</label>
             <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
               <div className="space-y-4">
                 <Select 
                   label={t('label.output_mode')}
                   value={formData.output_mode}
                   onChange={e => setFormData({...formData, output_mode: e.target.value as OutputMode})}
                   options={[
                     { value: OutputMode.Centralized, label: t('opt.mode_centralized') },
                     { value: OutputMode.InPlace, label: t('opt.mode_inplace') },
                     { value: OutputMode.Custom, label: t('opt.mode_custom') },
                   ]}
                 />
                 {formData.output_mode === OutputMode.Custom && (
                   <Input 
                      label={t('label.custom_path')}
                      placeholder="/mnt/data/..."
                      value={formData.output_path || ''}
                      onChange={e => setFormData({...formData, output_path: e.target.value})}
                      className="animate-in fade-in slide-in-from-top-2 duration-200"
                   />
                 )}
               </div>

               <div className="flex flex-col justify-end gap-3 pb-2">
                 <div className="flex items-center gap-2">
                    <input 
                      type="checkbox" 
                      id="dryRun"
                      checked={formData.dry_run}
                      onChange={e => setFormData({...formData, dry_run: e.target.checked})}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                    />
                    <label htmlFor="dryRun" className="text-sm text-slate-700 select-none cursor-pointer">{t('label.dry_run')}</label>
                 </div>
                 <div className="flex items-center gap-2">
                    <input 
                      type="checkbox" 
                      id="force"
                      checked={formData.force}
                      onChange={e => setFormData({...formData, force: e.target.checked})}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                    />
                    <label htmlFor="force" className="text-sm text-slate-700 select-none cursor-pointer">{t('label.force')}</label>
                 </div>
               </div>
             </div>
          </div>

          <div className="pt-4 flex gap-4">
             <Button type="submit" isLoading={submitting} className="flex-1">{t('action.create_run')}</Button>
             <Button type="button" variant="secondary" onClick={() => window.history.back()}>{t('action.cancel')}</Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
