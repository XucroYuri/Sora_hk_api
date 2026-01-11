
import React, { useState, useEffect } from 'react';
import { Task } from '../../types';
import { api } from '../../services/api';
import { useI18n } from '../../App';
import { Card, Button, Modal, Select, StatusBadge } from '../../components/ui';

// Result Card Component
const ResultCard: React.FC<{ task: Task; onViewDetails: (t: Task) => void }> = ({ task, onViewDetails }) => {
  const { t } = useI18n();
  return (
    <div className="group relative bg-white border border-slate-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
      {/* Video Thumbnail / Player */}
      <div className="aspect-video bg-slate-900 relative">
        {task.video_url ? (
          <video 
            src={task.video_url} 
            className="w-full h-full object-cover" 
            controls 
            preload="metadata"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-500 text-xs">
            {t('res.no_media')}
          </div>
        )}
      </div>

      {/* Info Body */}
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
           <span className="inline-block px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs font-mono font-medium">
             {t('res.task_prefix')}{task.id}
           </span>
           <span className="text-xs text-slate-400">
             {t('res.seg_prefix')}{task.segment_index}
           </span>
        </div>
        
        {/* Actions */}
        <div className="mt-4 flex items-center justify-between border-t border-slate-50 pt-3">
          <button 
             onClick={() => onViewDetails(task)}
             className="text-xs text-slate-500 hover:text-blue-600 font-medium"
          >
             {t('action.details')}
          </button>
          <a 
            href={task.video_url || '#'} 
            download 
            target="_blank"
            rel="noreferrer"
            className={`text-sm font-medium flex items-center gap-1 ${task.video_url ? 'text-blue-600 hover:text-blue-800' : 'text-slate-300 pointer-events-none'}`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            {t('action.download')}
          </a>
        </div>
      </div>
    </div>
  );
};

export const ResultsList: React.FC = () => {
  const { t } = useI18n();
  const [results, setResults] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Filter & Detail State
  const [isFilterOpen, setFilterOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [filterType, setFilterType] = useState('all');
  const [filterDate, setFilterDate] = useState('all');

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const data = await api.getResults();
        setResults(data);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, []);

  // Filter Logic
  const filteredResults = results.filter(task => {
    // 1. Media Type Filter
    if (filterType === 'video' && !task.video_url) return false;
    if (filterType === 'image' && task.video_url) return false; 

    // 2. Date Filter
    if (filterDate !== 'all' && task.created_at) {
      const taskDate = new Date(task.created_at);
      const now = new Date();
      
      if (filterDate === 'today') {
        if (taskDate.toDateString() !== now.toDateString()) return false;
      } else if (filterDate === 'week') {
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(now.getDate() - 7);
        if (taskDate < oneWeekAgo) return false;
      }
    }

    return true;
  });

  const downloadMetadata = (task: Task) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(task, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `${task.id}_metadata.json`);
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
           <h2 className="text-2xl font-bold text-slate-800">{t('title.results')}</h2>
           <p className="text-slate-500 text-sm mt-1">
             {loading ? '...' : `${filteredResults.length} ${t('res.generated_count')}`}
           </p>
        </div>
        <div className="flex gap-2">
           <Button variant="secondary" size="sm" onClick={() => setFilterOpen(true)}>{t('action.filter')}</Button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400">{t('res.loading')}</div>
      ) : filteredResults.length === 0 ? (
        <Card className="p-12 text-center text-slate-500">
          {t('res.empty')}
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredResults.map(task => (
            <ResultCard key={task.id} task={task} onViewDetails={setSelectedTask} />
          ))}
        </div>
      )}

      {/* Filter Modal */}
      <Modal 
        isOpen={isFilterOpen} 
        onClose={() => setFilterOpen(false)} 
        title={t('action.filter')}
      >
        <div className="space-y-4">
          <Select 
            label={t('filter.media_type')}
            options={[
              { value: 'all', label: t('filter.all_media') },
              { value: 'video', label: t('filter.video_only') },
            ]}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          />
           <Select 
            label={t('filter.date_range')}
            options={[
              { value: 'all', label: t('filter.all_time') },
              { value: 'today', label: t('filter.today') },
              { value: 'week', label: t('filter.week') },
            ]}
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
          />
          <div className="flex justify-end pt-4">
            <Button onClick={() => setFilterOpen(false)}>{t('action.apply_filter')}</Button>
          </div>
        </div>
      </Modal>

      {/* Metadata Detail Modal */}
      {selectedTask && (
        <Modal 
          isOpen={!!selectedTask} 
          onClose={() => setSelectedTask(null)} 
          title={`${t('action.details')}: ${selectedTask.id}`}
        >
          <div className="space-y-4 text-sm">
             <div>
                <label className="block text-slate-500 font-medium text-xs uppercase mb-1">{t('label.prompt')}</label>
                <div className="bg-slate-50 p-3 rounded border border-slate-100 max-h-40 overflow-y-auto whitespace-pre-wrap">
                  {selectedTask.full_prompt || t('res.na')}
                </div>
             </div>
             <div className="grid grid-cols-2 gap-4">
                <div>
                   <label className="block text-slate-500 font-medium text-xs uppercase mb-1">{t('col.status')}</label>
                   <StatusBadge status={selectedTask.status} label={t(`status.${selectedTask.status}` as any)} />
                </div>
                <div>
                   <label className="block text-slate-500 font-medium text-xs uppercase mb-1">{t('col.created')}</label>
                   <span className="text-slate-800">{selectedTask.created_at ? new Date(selectedTask.created_at).toLocaleString() : '-'}</span>
                </div>
             </div>
             <div className="pt-4 flex justify-between items-center border-t border-slate-100 mt-4">
                 <button 
                  onClick={() => downloadMetadata(selectedTask)}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
                 >
                   <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                   Download Metadata
                 </button>
                <Button variant="secondary" onClick={() => setSelectedTask(null)}>{t('action.cancel')}</Button>
             </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
