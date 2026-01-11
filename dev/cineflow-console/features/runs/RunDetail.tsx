
import React, { useState, useEffect } from 'react';
import { Task, RunStatus } from '../../types';
import { api } from '../../services/api';
import { useI18n } from '../../App';
import { Button, Card, StatusBadge, Modal, useToast } from '../../components/ui';

// Task Item Component
const TaskItem: React.FC<{ 
  task: Task; 
  onRetry: (id: string) => void; 
  onViewDetails: (t: Task) => void;
  isRetrying: boolean;
}> = ({ task, onRetry, onViewDetails, isRetrying }) => {
  const { t } = useI18n();
  return (
    <div className={`p-4 border rounded-lg bg-white flex gap-4 transition-all ${task.status === RunStatus.Failed || task.status === RunStatus.DownloadFailed ? 'border-red-200 bg-red-50/10' : 'border-slate-200 hover:border-blue-300'}`}>
       <div className="w-24 h-16 bg-slate-900 rounded flex items-center justify-center text-slate-500 relative group overflow-hidden">
          {task.video_url ? (
             <video src={task.video_url} className="w-full h-full object-cover rounded" />
          ) : (
             <span className="text-xs">No Video</span>
          )}
          {task.video_url && (
             <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
             </div>
          )}
       </div>
       <div className="flex-1 min-w-0">
          <div className="flex justify-between mb-1">
             <span className="font-mono text-xs text-slate-500">#{task.segment_index} · {task.id}</span>
             <StatusBadge status={task.status} label={t(`status.${task.status}` as any)} />
          </div>
          {task.error_msg ? (
            <div className="text-sm text-red-600 font-medium truncate" title={task.error_msg}>
              {task.error_code && <span className="font-mono bg-red-100 px-1 rounded text-xs mr-1">{task.error_code}</span>}
              {task.error_msg}
            </div>
          ) : (
            <div className="text-sm text-slate-400 truncate">{task.full_prompt || '-'}</div>
          )}
          
          <div className="mt-2 flex gap-2 items-center">
             <button 
               onClick={() => onViewDetails(task)}
               className="text-xs text-slate-500 hover:text-blue-600 font-medium border border-slate-200 rounded px-2 py-0.5 hover:border-blue-300 transition-colors"
             >
               {t('action.details')}
             </button>
             {task.video_url && <a href={task.video_url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">{t('action.download')}</a>}
             {task.retryable && (
               <button 
                 onClick={() => onRetry(task.id)}
                 disabled={isRetrying}
                 className="text-xs text-blue-600 hover:underline font-medium disabled:opacity-50 disabled:cursor-not-allowed"
               >
                 {isRetrying ? t('status.queued') : t('action.retry')}
               </button>
             )}
          </div>
       </div>
    </div>
  );
};

// --- Stats Component ---
const RunStatsHeader: React.FC<{ tasks: Task[] }> = ({ tasks }) => {
    const { t } = useI18n();
    const total = tasks.length;
    const completed = tasks.filter(t => t.status === RunStatus.Completed).length;
    const failed = tasks.filter(t => t.status === RunStatus.Failed || t.status === RunStatus.DownloadFailed).length;
    const running = tasks.filter(t => t.status === RunStatus.Running).length;
    const queued = tasks.filter(t => t.status === RunStatus.Queued).length;
    
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

    return (
        <Card className="mb-6">
            <div className="flex flex-col gap-4">
                <div className="flex justify-between items-end">
                    <div>
                        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">{t('label.run_progress')}</h3>
                        <div className="text-3xl font-bold text-slate-800">{percent}% <span className="text-sm font-normal text-slate-500">({completed}/{total})</span></div>
                    </div>
                    <div className="flex gap-4 text-sm">
                        <div className="flex flex-col items-center">
                             <span className="font-bold text-green-600">{completed}</span>
                             <span className="text-xs text-slate-500">{t('status.completed')}</span>
                        </div>
                        <div className="flex flex-col items-center">
                             <span className="font-bold text-blue-600">{running}</span>
                             <span className="text-xs text-slate-500">{t('status.running')}</span>
                        </div>
                        <div className="flex flex-col items-center">
                             <span className="font-bold text-slate-600">{queued}</span>
                             <span className="text-xs text-slate-500">{t('status.queued')}</span>
                        </div>
                        <div className="flex flex-col items-center">
                             <span className="font-bold text-red-600">{failed}</span>
                             <span className="text-xs text-slate-500">{t('status.failed')}</span>
                        </div>
                    </div>
                </div>
                {/* Visual Progress Bar */}
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex">
                    <div className="bg-green-500 h-full transition-all duration-500" style={{ width: `${(completed / total) * 100}%` }} />
                    <div className="bg-blue-500 h-full transition-all duration-500" style={{ width: `${(running / total) * 100}%` }} />
                    <div className="bg-red-500 h-full transition-all duration-500" style={{ width: `${(failed / total) * 100}%` }} />
                </div>
            </div>
        </Card>
    );
}

export const RunDetail: React.FC<{ id: string }> = ({ id }) => {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<'all' | 'failed_retryable'>('failed_retryable');
  const [retryingTasks, setRetryingTasks] = useState<Set<string>>(new Set());
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  // Auto-refresh logic
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    const fetchData = async () => {
      const data = await api.getRunTasks(id);
      setTasks(data);
      
      // Determine if we should poll: stop polling if all tasks are final
      const isOngoing = data.some(t => t.status === RunStatus.Running || t.status === RunStatus.Queued);
      
      if (!isOngoing) {
          clearInterval(interval);
      }
    };

    fetchData();
    interval = setInterval(fetchData, 3000); // 3s polling
    return () => clearInterval(interval);
  }, [id]);

  const handleRetry = async (taskId: string) => {
    setRetryingTasks(prev => new Set(prev).add(taskId));
    try {
      await api.retryTask(id, taskId);
      // Optimistic update
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: RunStatus.Queued } : t));
      showToast(t('msg.task_queued'), 'success');
    } catch (e) {
      showToast(t('error.generic'), 'error');
    } finally {
      setRetryingTasks(prev => {
        const next = new Set(prev);
        next.delete(taskId);
        return next;
      });
    }
  };

  const filteredTasks = tasks.filter(t => {
     if (filter === 'failed_retryable') {
         return (t.status === RunStatus.Failed || t.status === RunStatus.DownloadFailed) && t.retryable;
     }
     return true;
  });

  const downloadMetadata = (task: Task) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(task, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `${task.id}_metadata.json`);
    document.body.appendChild(downloadAnchorNode); 
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  return (
    <div className="space-y-6">
       <div className="flex items-center gap-4">
        <a href="#/runs" className="text-slate-500 hover:text-blue-600">
           <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        </a>
        <h2 className="text-2xl font-bold text-slate-800">Run: {id}</h2>
      </div>

      <RunStatsHeader tasks={tasks} />

      <div className="flex items-center justify-between">
        <div className="flex gap-2">
           <button 
             onClick={() => setFilter('failed_retryable')}
             className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${filter === 'failed_retryable' ? 'bg-red-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'}`}
           >
             {t('filter.failed_retryable')} ({tasks.filter(t => (t.status === RunStatus.Failed || t.status === RunStatus.DownloadFailed) && t.retryable).length})
           </button>
           <button 
             onClick={() => setFilter('all')}
             className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'}`}
           >
             {t('filter.all_status')} ({tasks.length})
           </button>
        </div>
        <Button size="sm" variant="secondary" onClick={() => window.location.reload()}>
           Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTasks.map(task => (
           <TaskItem 
             key={task.id} 
             task={task} 
             onRetry={handleRetry}
             onViewDetails={setSelectedTask}
             isRetrying={retryingTasks.has(task.id)}
           />
        ))}
        {filteredTasks.length === 0 && (
          <div className="col-span-full py-12 text-center text-slate-400">
            {filter === 'failed_retryable' ? t('res.empty') : t('res.empty')}
          </div>
        )}
      </div>

      {/* Task Metadata Modal */}
      {selectedTask && (
        <Modal 
          isOpen={!!selectedTask} 
          onClose={() => setSelectedTask(null)} 
          title={`Task Details: ${selectedTask.id}`}
        >
          <div className="space-y-4 text-sm">
             <div>
                <label className="block text-slate-500 font-medium text-xs uppercase mb-1">{t('label.prompt')}</label>
                <div className="bg-slate-50 p-3 rounded border border-slate-100 max-h-40 overflow-y-auto whitespace-pre-wrap">
                  {selectedTask.full_prompt || 'N/A'}
                </div>
             </div>
             <div className="grid grid-cols-2 gap-4">
                <div>
                   <label className="block text-slate-500 font-medium text-xs uppercase mb-1">{t('col.status')}</label>
                   <StatusBadge status={selectedTask.status} label={t(`status.${selectedTask.status}` as any)} />
                </div>
                {selectedTask.error_code && (
                  <div>
                    <label className="block text-slate-500 font-medium text-xs uppercase mb-1">{t('label.error_code')}</label>
                    <span className="font-mono text-red-600 bg-red-50 px-1 rounded">{selectedTask.error_code}</span>
                  </div>
                )}
             </div>
             {selectedTask.error_msg && (
               <div>
                  <label className="block text-slate-500 font-medium text-xs uppercase mb-1">{t('label.error_msg')}</label>
                  <p className="text-red-600">{selectedTask.error_msg}</p>
               </div>
             )}
             <div className="pt-4 flex justify-between items-center border-t border-slate-100 mt-4">
                 <button 
                  onClick={() => downloadMetadata(selectedTask)}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
                 >
                   <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                   {t('action.download_meta')}
                 </button>
                <Button variant="secondary" onClick={() => setSelectedTask(null)}>{t('action.cancel')}</Button>
             </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
