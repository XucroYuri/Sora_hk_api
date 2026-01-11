

import React, { useState, useEffect } from 'react';
import { Segment, Resolution, DurationOption } from '../../types';
import { api } from '../../services/api';
import { useI18n } from '../../App';
import { Button, Input, Select, Modal, TagInput, useToast } from '../../components/ui';

// Segment Card Component
const SegmentCard: React.FC<{ 
  seg: Segment; 
  onEdit: (s: Segment) => void;
  onImageUpload: (s: Segment, f: File) => void;
}> = ({ seg, onEdit, onImageUpload }) => {
  const { t } = useI18n();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onImageUpload(seg, e.target.files[0]);
    }
  };

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white hover:border-blue-300 transition-all shadow-sm">
      <div className="flex gap-4">
        {/* Index & Image */}
        <div className="w-32 flex-shrink-0 flex flex-col gap-2">
          <div className="aspect-video bg-slate-100 rounded-md flex items-center justify-center overflow-hidden border border-slate-100 relative group">
             {seg.image_url ? (
               <img src={seg.image_url} alt="Reference" className="w-full h-full object-cover" />
             ) : (
               <div className="flex flex-col items-center justify-center p-2 text-center">
                 <svg className="w-6 h-6 text-slate-300 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                 <span className="text-slate-400 text-[10px]">{t('res.no_ref')}</span>
               </div>
             )}
             
             {/* Upload Overlay */}
             <label className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center cursor-pointer transition-opacity">
                <span className="text-white text-xs font-medium">{t('action.upload_ref')}</span>
                <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
             </label>
          </div>
          <div className="text-center font-mono text-xs text-slate-500">#{seg.segment_index}</div>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3">
          <div className="grid grid-cols-2 gap-4">
             <div>
               <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1 block">{t('label.prompt')}</label>
               <p className="text-sm text-slate-800 bg-slate-50 p-2 rounded border border-slate-100 line-clamp-2" title={seg.prompt_text}>{seg.prompt_text}</p>
             </div>
             <div className="space-y-2">
                <div>
                   <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1 block">{t('label.intent')}</label>
                   <p className="text-xs text-slate-600 truncate">{seg.director_intent || '-'}</p>
                </div>
                <div className="flex gap-2">
                  <span className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600">{seg.duration_seconds}s</span>
                  <span className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600 uppercase">{seg.resolution === 'horizontal' ? '16:9' : '9:16'}</span>
                  {seg.is_pro && <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-xs font-bold">PRO</span>}
                </div>
             </div>
          </div>
          
          {/* Assets */}
          <div className="border-t border-slate-100 pt-2 flex gap-4 text-xs">
            <div className="text-slate-500 max-w-[120px] truncate" title={seg.asset.scene || ''}><span className="font-semibold">{t('label.scene')}:</span> {seg.asset.scene || t('res.na')}</div>
            <div className="text-slate-500 max-w-[150px] truncate" title={seg.asset.props.join(', ')}><span className="font-semibold">{t('label.props')}:</span> {seg.asset.props.join(', ') || t('res.na')}</div>
            <div className="text-slate-500 max-w-[150px] truncate" title={seg.asset.characters.map(c => c.name).join(', ')}><span className="font-semibold">{t('label.chars')}:</span> {seg.asset.characters.map(c => c.name).join(', ') || t('res.na')}</div>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex flex-col gap-2">
           <Button variant="secondary" size="sm" onClick={() => onEdit(seg)}>{t('action.edit')}</Button>
        </div>
      </div>
    </div>
  );
};

export const StoryboardDetail: React.FC<{ id: string }> = ({ id }) => {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [segments, setSegments] = useState<Segment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Edit Modal State
  const [editingSegment, setEditingSegment] = useState<Segment | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchSegments();
  }, [id]);

  const fetchSegments = async () => {
    setLoading(true);
    const data = await api.getStoryboardSegments(id);
    setSegments(data);
    setLoading(false);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSegment) return;
    
    setIsSaving(true);
    try {
      await api.updateSegment(editingSegment);
      setSegments(prev => prev.map(s => s.id === editingSegment.id ? editingSegment : s));
      setEditingSegment(null);
      showToast(t('msg.save_success'), 'success');
    } catch (err) {
      console.error("Failed to update segment", err);
      showToast(t('error.generic'), 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleImageUpload = async (seg: Segment, file: File) => {
    try {
      const newUrl = await api.uploadSegmentImage(seg.id, file);
      setSegments(prev => prev.map(s => s.id === seg.id ? { ...s, image_url: newUrl } : s));
      showToast(t('msg.upload_success'), 'success');
    } catch (err) {
      showToast(t('error.upload_failed'), 'error');
    }
  };

  // Tag Input Helpers
  const addProp = (prop: string) => {
    if (editingSegment && !editingSegment.asset.props.includes(prop)) {
        setEditingSegment({
            ...editingSegment,
            asset: { ...editingSegment.asset, props: [...editingSegment.asset.props, prop] }
        });
    }
  };

  const removeProp = (prop: string) => {
    if (editingSegment) {
        setEditingSegment({
            ...editingSegment,
            asset: { ...editingSegment.asset, props: editingSegment.asset.props.filter(p => p !== prop) }
        });
    }
  };

  const addChar = (input: string) => {
      // Regex to split Name and optional ID (Name @ID)
      const match = input.match(/^(.*?)\s*(@[a-zA-Z0-9_]+)$/);
      const name = match ? match[1] : input;
      const id = match ? match[2] : undefined;
      
      const newChar = { name: name.trim(), id };
      
      if (editingSegment && newChar.name) {
          // Avoid duplicates by name
          if (!editingSegment.asset.characters.some(c => c.name === newChar.name)) {
              setEditingSegment({
                  ...editingSegment,
                  asset: { ...editingSegment.asset, characters: [...editingSegment.asset.characters, newChar] }
              });
          }
      }
  };

  const removeChar = (charDisplay: string) => {
      if (editingSegment) {
          setEditingSegment({
              ...editingSegment,
              asset: { 
                ...editingSegment.asset, 
                characters: editingSegment.asset.characters.filter(c => {
                  const display = c.id ? `${c.name} ${c.id}` : c.name;
                  return display !== charDisplay;
                }) 
              }
          });
      }
  };


  const filteredSegments = segments.filter(s => 
    s.prompt_text.toLowerCase().includes(searchQuery.toLowerCase()) || 
    s.segment_index.toString().includes(searchQuery)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <a href="#/storyboards" className="text-slate-500 hover:text-blue-600">
           <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        </a>
        <h2 className="text-2xl font-bold text-slate-800">Storyboard: {id}</h2>
        <div className="flex-1"></div>
        <Button onClick={() => window.location.hash = `#/runs/create`}>{t('action.create_run')}</Button>
      </div>

      {/* Search Bar */}
      <div className="relative">
         <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
         </div>
         <input 
           type="text" 
           placeholder={t('label.search_hint')}
           className="pl-10 block w-full rounded-lg border border-slate-300 bg-white py-2 px-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent sm:text-sm"
           value={searchQuery}
           onChange={(e) => setSearchQuery(e.target.value)}
         />
      </div>

      <div className="space-y-4">
         {loading ? <div className="text-center py-10">{t('state.loading')}</div> : 
          filteredSegments.length === 0 ? <div className="text-center py-10 text-slate-400">{t('state.empty')}</div> :
          filteredSegments.map(seg => (
           <SegmentCard 
             key={seg.id} 
             seg={seg} 
             onEdit={setEditingSegment}
             onImageUpload={handleImageUpload}
           />
         ))}
      </div>

      {/* Edit Modal */}
      {editingSegment && (
        <Modal 
          isOpen={!!editingSegment} 
          onClose={() => setEditingSegment(null)} 
          title={`${t('action.edit')} #${editingSegment.segment_index}`}
        >
          <form onSubmit={handleSaveEdit} className="space-y-4 max-h-[80vh] overflow-y-auto pr-2 no-scrollbar">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">{t('label.prompt')}</label>
              <textarea 
                className="w-full h-24 p-3 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                value={editingSegment.prompt_text}
                onChange={e => setEditingSegment({...editingSegment, prompt_text: e.target.value})}
              />
            </div>
            
            <Input 
              label={t('label.intent')}
              value={editingSegment.director_intent || ''}
              onChange={e => setEditingSegment({...editingSegment, director_intent: e.target.value})}
            />

            <div className="grid grid-cols-2 gap-4">
               <Select 
                 label={t('label.duration')}
                 options={[4, 8, 10, 12, 15, 25].map(v => ({ value: v, label: `${v}s` }))}
                 value={editingSegment.duration_seconds}
                 onChange={e => setEditingSegment({...editingSegment, duration_seconds: Number(e.target.value) as DurationOption})}
               />
               <Select 
                 label={t('label.resolution')}
                 options={[{value: Resolution.Horizontal, label: 'Horizontal (16:9)'}, {value: Resolution.Vertical, label: 'Vertical (9:16)'}]}
                 value={editingSegment.resolution}
                 onChange={e => setEditingSegment({...editingSegment, resolution: e.target.value as Resolution})}
               />
            </div>

            <div className="flex items-center gap-2 pt-2">
               <input 
                 type="checkbox" 
                 id="isPro"
                 checked={editingSegment.is_pro}
                 onChange={e => setEditingSegment({...editingSegment, is_pro: e.target.checked})}
                 className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
               />
               <label htmlFor="isPro" className="text-sm font-medium text-slate-700">{t('label.is_pro')}</label>
            </div>

            {/* Asset Editing Section (Visualized) */}
            <div className="border-t border-slate-100 pt-4 mt-4">
              <h4 className="text-sm font-bold text-slate-800 mb-3 uppercase tracking-wider">{t('label.assets')}</h4>
              
              <Input
                label={t('label.scene')}
                placeholder="e.g. Cyberpunk City Street"
                value={editingSegment.asset.scene || ''}
                onChange={e => setEditingSegment({
                    ...editingSegment,
                    asset: { ...editingSegment.asset, scene: e.target.value }
                })}
              />
              
              <div className="mt-4 space-y-4">
                  <TagInput
                    label={t('label.props')}
                    tags={editingSegment.asset.props}
                    placeholder={t('label.tag_placeholder')}
                    onAdd={addProp}
                    onRemove={removeProp}
                  />
                  
                  <TagInput
                    label={t('label.chars')}
                    tags={editingSegment.asset.characters.map(c => c.id ? `${c.name} ${c.id}` : c.name)}
                    placeholder={t('label.chars_hint')}
                    onAdd={addChar}
                    onRemove={removeChar}
                  />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 mt-4">
              <Button type="button" variant="secondary" onClick={() => setEditingSegment(null)}>{t('action.cancel')}</Button>
              <Button type="submit" isLoading={isSaving}>{t('action.save')}</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
