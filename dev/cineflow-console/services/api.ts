
import { Storyboard, Segment, Run, RunStatus, Task, Model, Resolution, Provider, RunCreateRequest } from '../types';

// --- Mock Data Store ---
let MOCK_STORYBOARDS: Storyboard[] = [
  { id: 'sb_1', name: 'Cyberpunk_City_Demo.json', created_at: '2026-01-01T10:00:00Z', segment_count: 5 },
  { id: 'sb_2', name: 'Nature_Documentary.json', created_at: '2026-01-02T09:30:00Z', segment_count: 12 },
];

let MOCK_SEGMENTS: Record<string, Segment[]> = {
  'sb_1': Array.from({ length: 5 }).map((_, i) => ({
    id: `seg_1_${i}`,
    segment_index: i + 1,
    prompt_text: `Scene ${i + 1}: A futuristic cityscape with neon lights.`,
    director_intent: 'Establishing shot, wide angle.',
    image_url: `https://picsum.photos/seed/seg1_${i}/300/200`,
    duration_seconds: 10,
    resolution: Resolution.Horizontal,
    is_pro: i % 2 === 0,
    asset: { characters: [{name: "Alice", id: "@alice"}], scene: 'Neon City', props: ['Hologram', 'Cyberbike'] }
  })),
};

let MOCK_RUNS: Run[] = [
  { id: 'run_1', storyboard_id: 'sb_1', storyboard_name: 'Cyberpunk_City_Demo.json', model_id: 'sora-2', status: RunStatus.Completed, total_tasks: 10, completed: 10, failed: 0, download_failed: 0, created_at: '2026-01-02T12:00:00Z' },
  { id: 'run_2', storyboard_id: 'sb_1', storyboard_name: 'Cyberpunk_City_Demo.json', model_id: 'veo-2', status: RunStatus.Running, total_tasks: 20, completed: 5, failed: 2, download_failed: 0, created_at: '2026-01-02T14:00:00Z' },
];

const MOCK_TASKS: Record<string, Task[]> = {
  'run_1': Array.from({ length: 10 }).map((_, i) => ({
    id: `task_1_${i}`,
    run_id: 'run_1',
    status: RunStatus.Completed,
    video_url: 'https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4',
    metadata_url: '#',
    full_prompt: 'Full processed prompt...',
    error_code: null,
    error_msg: null,
    retryable: false,
    segment_index: (i % 5) + 1,
    created_at: '2026-01-02T12:05:00Z'
  })),
  'run_2': Array.from({ length: 20 }).map((_, i) => ({
    id: `task_2_${i}`,
    run_id: 'run_2',
    status: i < 5 ? RunStatus.Completed : (i < 7 ? RunStatus.Failed : RunStatus.Queued),
    video_url: i < 5 ? 'https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4' : null,
    metadata_url: '#',
    full_prompt: 'Full processed prompt...',
    error_code: i >= 5 && i < 7 ? (i === 5 ? 'rate_limited' : 'server_error') : null,
    error_msg: i >= 5 && i < 7 ? (i === 5 ? 'Too many requests' : 'GPU Timeout') : null,
    retryable: i >= 5 && i < 7,
    segment_index: (i % 5) + 1,
    created_at: '2026-01-02T14:10:00Z'
  })),
};

const MOCK_MODELS: Model[] = [
  { id: 'sora-2', display_name: 'Sora 2.0', description: 'Standard high-quality generation', enabled: true },
  { id: 'veo-2', display_name: 'Veo 2 (Fast)', description: 'Low latency, good for drafts', enabled: true },
  { id: 'imagen-3', display_name: 'Imagen 3 (Motion)', description: 'Image-to-video specialized', enabled: false },
];

const MOCK_PROVIDERS: Provider[] = [
  { id: 'openai', name: 'OpenAI Platform', type: 'External', priority: 1, weight: 1, enabled: true },
  { id: 'google-vertex', name: 'Google Vertex AI', type: 'External', priority: 2, weight: 2, enabled: true },
  { id: 'local-cluster', name: 'Local H100 Cluster', type: 'Internal', priority: 0, weight: 10, enabled: true },
];

// --- API Methods ---

export const api = {
  getStoryboards: async (): Promise<Storyboard[]> => {
    await new Promise(r => setTimeout(r, 500));
    return [...MOCK_STORYBOARDS];
  },

  getStoryboardSegments: async (id: string): Promise<Segment[]> => {
    await new Promise(r => setTimeout(r, 600));
    return MOCK_SEGMENTS[id] || [];
  },

  updateSegment: async (storyboardId: string, segment: Segment): Promise<void> => {
    await new Promise(r => setTimeout(r, 500));
    const segments = MOCK_SEGMENTS[storyboardId];
    const index = segments.findIndex(s => s.id === segment.id);
    if (index !== -1) {
      segments[index] = segment;
    }
  },

  uploadSegmentImage: async (storyboardId: string, segmentId: string, file: File): Promise<string> => {
    await new Promise(r => setTimeout(r, 1000));
    const mockUrl = URL.createObjectURL(file);
    const segments = MOCK_SEGMENTS[storyboardId];
    const seg = segments.find(s => s.id === segmentId);
    if (seg) seg.image_url = mockUrl;
    return mockUrl;
  },

  uploadStoryboard: async (file: File): Promise<Storyboard> => {
    await new Promise(r => setTimeout(r, 1000));
    const newId = `sb_${Date.now()}`;
    const newSb: Storyboard = {
      id: newId,
      name: file.name,
      created_at: new Date().toISOString(),
      segment_count: 3
    };
    MOCK_STORYBOARDS.unshift(newSb);
    MOCK_SEGMENTS[newId] = Array.from({ length: 3 }).map((_, i) => ({
      id: `seg_${newId}_${i}`,
      segment_index: i + 1,
      prompt_text: `Imported scene ${i + 1}`,
      director_intent: null,
      image_url: null,
      duration_seconds: 10,
      resolution: Resolution.Horizontal,
      is_pro: false,
      asset: { characters: [], scene: null, props: [] }
    }));
    return newSb;
  },

  deleteStoryboard: async (id: string): Promise<void> => {
    await new Promise(r => setTimeout(r, 500));
    MOCK_STORYBOARDS = MOCK_STORYBOARDS.filter(s => s.id !== id);
    delete MOCK_SEGMENTS[id];
  },

  getRuns: async (): Promise<Run[]> => {
    await new Promise(r => setTimeout(r, 500));
    return [...MOCK_RUNS];
  },

  getRunTasks: async (runId: string): Promise<Task[]> => {
    await new Promise(r => setTimeout(r, 500));
    return MOCK_TASKS[runId] || [];
  },

  createRun: async (config: RunCreateRequest): Promise<Run> => {
    await new Promise(r => setTimeout(r, 800));
    
    // Simulate validation
    if (!config.model_id) throw new Error("Validation Error: model_id required");

    const newRun: Run = {
      id: `run_${Date.now()}`,
      storyboard_id: config.storyboard_id,
      storyboard_name: MOCK_STORYBOARDS.find(s => s.id === config.storyboard_id)?.name,
      model_id: config.model_id,
      status: RunStatus.Queued,
      total_tasks: config.gen_count * (config.range ? 1 : 5), // Rough estimate logic
      completed: 0,
      failed: 0,
      download_failed: 0,
      created_at: new Date().toISOString()
    };
    MOCK_RUNS.unshift(newRun);
    MOCK_TASKS[newRun.id] = Array.from({ length: newRun.total_tasks }).map((_, i) => ({
      id: `task_${newRun.id}_${i}`,
      run_id: newRun.id,
      status: RunStatus.Queued,
      video_url: null,
      metadata_url: null,
      full_prompt: null,
      error_code: null,
      error_msg: null,
      retryable: false,
      segment_index: 1
    }));
    return newRun;
  },

  retryTask: async (runId: string, taskId: string): Promise<void> => {
    await new Promise(r => setTimeout(r, 500));
    const tasks = MOCK_TASKS[runId];
    const task = tasks.find(t => t.id === taskId);
    if (task) {
      task.status = RunStatus.Queued;
      task.error_code = null;
      task.error_msg = null;
      task.retryable = false;
    }
  },

  deleteRun: async (id: string): Promise<void> => {
    await new Promise(r => setTimeout(r, 500));
    MOCK_RUNS = MOCK_RUNS.filter(r => r.id !== id);
    delete MOCK_TASKS[id];
  },

  getResults: async (): Promise<Task[]> => {
    await new Promise(r => setTimeout(r, 700));
    const allTasks = Object.values(MOCK_TASKS).flat();
    return allTasks.filter(t => t.status === RunStatus.Completed);
  },

  getModels: async (): Promise<Model[]> => {
    await new Promise(r => setTimeout(r, 300));
    return [...MOCK_MODELS];
  },

  toggleModel: async (id: string, enabled: boolean): Promise<void> => {
    const model = MOCK_MODELS.find(m => m.id === id);
    if (model) model.enabled = enabled;
  },

  getProviders: async (): Promise<Provider[]> => {
    await new Promise(r => setTimeout(r, 300));
    return [...MOCK_PROVIDERS];
  },

  toggleProvider: async (id: string, enabled: boolean): Promise<void> => {
    await new Promise(r => setTimeout(r, 300));
    const provider = MOCK_PROVIDERS.find(p => p.id === id);
    if (provider) provider.enabled = enabled;
  }
};
