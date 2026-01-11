import {
  Storyboard,
  Segment,
  Run,
  RunStatus,
  Task,
  Model,
  Provider,
  RunCreateRequest,
  Asset,
} from '../types';

type Paginated<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || 'http://127.0.0.1:8088/api/v1';
const API_ORIGIN = API_BASE.replace(/\/api\/v1\/?$/, '');

const getAuthToken = (): string | null => {
  const envToken = (import.meta as any).env?.VITE_AUTH_TOKEN;
  if (envToken) {
    return envToken as string;
  }
  return window.localStorage.getItem('auth_token');
};

const resolveUrl = (url?: string | null): string | null => {
  if (!url) return null;
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) {
    return url;
  }
  if (url.startsWith('/uploads')) {
    return `${API_ORIGIN}${url}`;
  }
  if (url.startsWith('/api/')) {
    return `${API_ORIGIN}${url}`;
  }
  return `${API_BASE}${url.startsWith('/') ? url : `/${url}`}`;
};

const requestJson = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let payload: any = null;
    try {
      payload = await res.json();
    } catch {
      payload = { message: await res.text() };
    }
    const message = payload?.message || `Request failed with ${res.status}`;
    const err = new Error(message);
    (err as any).code = payload?.code;
    (err as any).details = payload?.details;
    throw err;
  }
  if (res.status === 204) {
    return null as T;
  }
  return (await res.json()) as T;
};

const normalizeAsset = (asset?: Asset | null): Asset => ({
  characters: asset?.characters || [],
  scene: asset?.scene ?? null,
  props: asset?.props || [],
});

const normalizeSegment = (segment: Segment): Segment => ({
  ...segment,
  director_intent: segment.director_intent ?? null,
  image_url: resolveUrl(segment.image_url),
  asset: normalizeAsset(segment.asset),
});

const normalizeTask = (task: Task, runId?: string): Task => ({
  ...task,
  run_id: task.run_id || runId,
  video_url: resolveUrl(task.video_url),
  metadata_url: resolveUrl(task.metadata_url || `/api/v1/tasks/${task.id}/metadata`),
  retryable: task.retryable ?? false,
});

const unwrap = <T>(payload: Paginated<T>): T[] => payload.items || [];

const fetchAllPages = async <T>(path: string, pageSize = 200): Promise<T[]> => {
  const items: T[] = [];
  let page = 1;
  while (true) {
    const joiner = path.includes('?') ? '&' : '?';
    const payload = await requestJson<Paginated<T>>(
      `${path}${joiner}page=${page}&page_size=${pageSize}`,
    );
    items.push(...unwrap(payload));
    if (items.length >= payload.total || payload.items.length === 0) {
      break;
    }
    page += 1;
  }
  return items;
};

export const api = {
  getStoryboards: async (): Promise<Storyboard[]> => {
    return fetchAllPages<Storyboard>('/storyboards?sort=created_at&order=desc');
  },

  getStoryboardSegments: async (id: string): Promise<Segment[]> => {
    const segments = await fetchAllPages<Segment>(
      `/storyboards/${id}/segments?sort=segment_index&order=asc`,
    );
    return segments.map(normalizeSegment);
  },

  updateSegment: async (segment: Segment): Promise<void> => {
    await requestJson<Segment>(`/segments/${segment.id}`, {
      method: 'PATCH',
      body: JSON.stringify({
        prompt_text: segment.prompt_text,
        director_intent: segment.director_intent,
        image_url: segment.image_url,
        duration_seconds: segment.duration_seconds,
        resolution: segment.resolution,
        is_pro: segment.is_pro,
        asset: segment.asset,
      }),
    });
  },

  uploadSegmentImage: async (segmentId: string, file: File): Promise<string> => {
    const form = new FormData();
    form.append('file', file);
    const data = await requestJson<{ image_url: string }>(`/segments/${segmentId}/assets/start-image`, {
      method: 'POST',
      body: form,
    });
    return resolveUrl(data.image_url) || data.image_url;
  },

  uploadStoryboard: async (file: File): Promise<Storyboard> => {
    const form = new FormData();
    form.append('file', file);
    return requestJson<Storyboard>('/storyboards', {
      method: 'POST',
      body: form,
    });
  },

  getRuns: async (): Promise<Run[]> => {
    return fetchAllPages<Run>('/runs?sort=created_at&order=desc');
  },

  getRunTasks: async (runId: string): Promise<Task[]> => {
    const tasks = await fetchAllPages<Task>(
      `/runs/${runId}/tasks?sort=segment_index&order=asc`,
    );
    return tasks.map((task) => normalizeTask(task, runId));
  },

  createRun: async (config: RunCreateRequest): Promise<Run> => {
    const data = await requestJson<Run>('/runs', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return { ...data, storyboard_id: config.storyboard_id, model_id: config.model_id };
  },

  retryTask: async (taskId: string): Promise<Task> => {
    const data = await requestJson<Task>(`/tasks/${taskId}/retry`, { method: 'POST' });
    return normalizeTask(data);
  },

  getTaskMetadata: async (task: Task): Promise<Record<string, unknown>> => {
    const url = resolveUrl(task.metadata_url || `/api/v1/tasks/${task.id}/metadata`);
    if (!url) {
      throw new Error('metadata_url is unavailable');
    }
    const token = getAuthToken();
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!res.ok) {
      throw new Error(`Failed to download metadata (${res.status})`);
    }
    return res.json();
  },

  getResults: async (): Promise<Task[]> => {
    const runs = await api.getRuns();
    const tasksByRun = await Promise.all(
      runs.map(async (run) => {
        const tasks = await api.getRunTasks(run.id);
        return tasks.map((task) => ({ ...task, created_at: task.created_at || run.created_at }));
      }),
    );
    return tasksByRun.flat().filter((task) => task.status === RunStatus.Completed);
  },

  getModels: async (): Promise<Model[]> => {
    return fetchAllPages<Model>('/models?sort=id&order=asc');
  },

  getAdminModels: async (): Promise<Model[]> => {
    return fetchAllPages<Model>('/admin/models?sort=id&order=asc');
  },

  toggleModel: async (id: string, enabled: boolean): Promise<Model> => {
    return requestJson<Model>(`/admin/models/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    });
  },

  getProviders: async (): Promise<Provider[]> => {
    return fetchAllPages<Provider>('/admin/providers?sort=id&order=asc');
  },

  toggleProvider: async (id: string, enabled: boolean): Promise<Provider> => {
    return requestJson<Provider>(`/admin/providers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    });
  },
};
