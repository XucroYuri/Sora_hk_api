

// --- Global Types (The Contract) ---

export enum Resolution {
  Horizontal = 'horizontal',
  Vertical = 'vertical',
}

export type DurationOption = 4 | 8 | 10 | 12 | 15 | 25;

export interface Character {
  name: string;
  id?: string; // Format: @[a-zA-Z0-9_]+
}

export interface Asset {
  characters: Character[];
  scene: string | null;
  props: string[];
}

export interface Segment {
  id: string;
  segment_index: number;
  prompt_text: string;
  director_intent: string | null;
  image_url: string | null;
  duration_seconds: DurationOption;
  resolution: Resolution;
  is_pro: boolean;
  asset: Asset;
}

export interface Storyboard {
  id: string;
  name: string;
  created_at: string;
  segment_count: number;
  segments?: Segment[]; // Optional for list view
}

export enum RunStatus {
  Queued = 'queued',
  Running = 'running',
  Completed = 'completed',
  Failed = 'failed',
  DownloadFailed = 'download_failed',
}

export enum OutputMode {
  Centralized = 'centralized',
  InPlace = 'in_place',
  Custom = 'custom',
}

export interface RunCreateRequest {
  storyboard_id: string;
  model_id: string;
  gen_count: number;
  concurrency: number;
  range: string;
  output_mode: OutputMode;
  output_path?: string;
  dry_run: boolean;
  force: boolean;
}

export interface Run {
  id: string;
  storyboard_id?: string;
  storyboard_name?: string;
  model_id?: string;
  status: RunStatus;
  total_tasks: number;
  completed: number;
  failed: number;
  download_failed: number;
  created_at: string;
}

export type TaskErrorCode = 
  | 'content_policy' 
  | 'validation_error' 
  | 'rate_limited' 
  | 'timeout' 
  | 'quota_exceeded' 
  | 'unauthorized' 
  | 'forbidden' 
  | 'dependency_error' 
  | 'server_error' 
  | 'unknown_error' 
  | 'download_failed' 
  | 'no_provider';

export interface Task {
  id: string;
  run_id?: string;
  status: RunStatus;
  video_url: string | null;
  metadata_url?: string | null;
  full_prompt: string | null;
  error_code: TaskErrorCode | null;
  error_msg: string | null;
  retryable?: boolean | null;
  segment_index: number;
  created_at?: string;
}

export interface Model {
  id: string;
  display_name: string;
  description?: string | null;
  enabled: boolean;
}

export interface Provider {
  id: string;
  display_name: string;
  priority: number;
  weight: number;
  enabled: boolean;
  supports_image_to_video: boolean;
  supported_durations: DurationOption[];
  supported_resolutions: Resolution[];
  supports_pro: boolean;
}

// i18n Types
export type Locale = 'zh-CN' | 'en-US';

export type I18nKeys =
  | 'app.title'
  | 'nav.dashboard'
  | 'nav.storyboards'
  | 'nav.runs'
  | 'nav.results'
  | 'nav.settings'
  | 'action.import'
  | 'action.create_run'
  | 'action.save'
  | 'action.cancel'
  | 'action.delete'
  | 'action.retry'
  | 'action.view'
  | 'action.edit'
  | 'action.filter'
  | 'action.download'
  | 'action.download_meta'
  | 'action.enable'
  | 'action.disable'
  | 'action.details'
  | 'action.upload_ref'
  | 'action.upload_click'
  | 'action.apply_filter'
  | 'action.clear_filter'
  | 'action.connect'
  | 'action.disconnect'
  | 'action.copy_link'
  | 'status.queued'
  | 'status.running'
  | 'status.completed'
  | 'status.failed'
  | 'status.download_failed'
  | 'status.active'
  | 'status.disabled'
  | 'status.connected'
  | 'status.disconnected'
  | 'label.model'
  | 'label.concurrency'
  | 'label.count'
  | 'label.range'
  | 'label.range_hint'
  | 'label.provider'
  | 'label.priority'
  | 'label.weight'
  | 'label.language'
  | 'label.prompt'
  | 'label.intent'
  | 'label.duration'
  | 'label.resolution'
  | 'label.is_pro'
  | 'label.assets'
  | 'label.scene'
  | 'label.props'
  | 'label.chars'
  | 'label.chars_hint'
  | 'label.output_mode'
  | 'label.custom_path'
  | 'label.dry_run'
  | 'label.force'
  | 'label.exec_options'
  | 'label.search_hint'
  | 'label.system_version'
  | 'label.tag_placeholder'
  | 'label.run_progress'
  | 'label.error_code'
  | 'label.error_msg'
  | 'opt.mode_centralized'
  | 'opt.mode_inplace'
  | 'opt.mode_custom'
  | 'msg.upload_success'
  | 'msg.create_run_success'
  | 'msg.save_success'
  | 'msg.confirm_delete'
  | 'msg.task_queued'
  | 'error.upload_failed'
  | 'error.delete_failed'
  | 'error.generic'
  | 'error.schema_validation'
  | 'dash.recent_runs'
  | 'dash.stats_overview'
  | 'dash.active_tasks'
  | 'dash.total_runs'
  | 'dash.success_rate'
  | 'dash.welcome'
  | 'title.results'
  | 'title.settings'
  | 'tab.general'
  | 'tab.models'
  | 'tab.providers'
  | 'col.model_name'
  | 'col.description'
  | 'col.status'
  | 'col.actions'
  | 'col.type'
  | 'col.capabilities'
  | 'col.id'
  | 'col.name'
  | 'col.segments'
  | 'col.created'
  | 'col.progress'
  | 'col.tasks'
  | 'res.no_media'
  | 'res.no_ref'
  | 'res.na'
  | 'res.task_prefix'
  | 'res.seg_prefix'
  | 'res.loading'
  | 'res.empty'
  | 'res.generated_count'
  | 'filter.media_type'
  | 'filter.all_media'
  | 'filter.video_only'
  | 'filter.date_range'
  | 'filter.all_time'
  | 'filter.today'
  | 'filter.week'
  | 'filter.status'
  | 'filter.all_status'
  | 'filter.failed_retryable'
  | 'state.loading'
  | 'state.empty'
  | 'file.storyboard_json';

export interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: I18nKeys, params?: Record<string, string | number>) => string;
}
