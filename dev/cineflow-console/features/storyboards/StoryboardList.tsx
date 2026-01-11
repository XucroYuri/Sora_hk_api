
import React, { useState, useEffect } from 'react';
import { Storyboard } from '../../types';
import { api } from '../../services/api';
import { useI18n } from '../../App';
import { Button, Card, Modal, useToast } from '../../components/ui';

export const StoryboardList: React.FC = () => {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [storyboards, setStoryboards] = useState<Storyboard[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploadModalOpen, setUploadModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const data = await api.getStoryboards();
      setStoryboards(data);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploadError(null);
    setIsUploading(true);
    const fileInput = (document.getElementById('file-upload') as HTMLInputElement);
    const file = fileInput?.files?.[0];
    
    if (file) {
      try {
        await api.uploadStoryboard(file);
        setUploadModalOpen(false);
        showToast(t('msg.upload_success'), 'success');
        fetchData();
      } catch (err) {
        console.error(err);
        setUploadError(t('error.upload_failed'));
      } finally {
        setIsUploading(false);
      }
    } else {
        setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm(t('msg.confirm_delete'))) {
      try {
        await api.deleteStoryboard(id);
        setStoryboards(prev => prev.filter(s => s.id !== id));
        showToast(t('msg.save_success'), 'success');
      } catch (e) {
        showToast(t('error.delete_failed'), 'error');
      }
    }
  };

  const openUploadModal = () => {
      setUploadError(null);
      setUploadModalOpen(true);
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800">{t('nav.storyboards')}</h2>
        <Button onClick={openUploadModal}>
          <span className="mr-2">+</span> {t('action.import')}
        </Button>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-100 uppercase text-xs font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-4">{t('col.id')}</th>
                <th className="px-6 py-4">{t('col.name')}</th>
                <th className="px-6 py-4">{t('col.segments')}</th>
                <th className="px-6 py-4">{t('col.created')}</th>
                <th className="px-6 py-4 text-right">{t('col.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr><td colSpan={5} className="px-6 py-8 text-center">{t('state.loading')}</td></tr>
              ) : storyboards.map((sb) => (
                <tr key={sb.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs">{sb.id}</td>
                  <td className="px-6 py-4 font-medium text-slate-900">{sb.name}</td>
                  <td className="px-6 py-4">{sb.segment_count}</td>
                  <td className="px-6 py-4">{new Date(sb.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <a href={`#/storyboards/${sb.id}`} className="text-blue-600 hover:text-blue-800 font-medium">{t('action.view')}</a>
                    <button 
                      onClick={() => handleDelete(sb.id)}
                      className="text-red-500 hover:text-red-700 font-medium text-xs ml-2"
                    >
                      {t('action.delete')}
                    </button>
                  </td>
                </tr>
              ))}
              {!isLoading && storyboards.length === 0 && (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-400">{t('state.empty')}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Modal 
        isOpen={isUploadModalOpen} 
        onClose={() => setUploadModalOpen(false)} 
        title={t('action.import')}
      >
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors relative">
            <input id="file-upload" type="file" accept=".json" className="hidden" onChange={() => setUploadError(null)} />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
               <svg className="w-10 h-10 text-slate-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
               <span className="text-blue-600 font-medium">{t('action.upload_click')}</span>
               <span className="text-slate-400 text-sm mt-1">{t('file.storyboard_json') || 'storyboard.json'}</span>
            </label>
          </div>
          
          {uploadError && (
              <div className="bg-red-50 border border-red-200 text-red-600 text-sm p-3 rounded-md flex items-start gap-2">
                  <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>{uploadError}</span>
              </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={() => setUploadModalOpen(false)}>{t('action.cancel')}</Button>
            <Button type="submit" isLoading={isUploading}>{t('action.import')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
