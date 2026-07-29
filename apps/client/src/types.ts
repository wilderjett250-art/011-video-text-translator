export type VideoMetadata = {
  width: number;
  height: number;
  fps: number;
  frame_count: number;
  duration_sec: number;
  has_audio: boolean;
};

export type FrameAsset = {
  id: string;
  timestamp_sec: number;
  frame_index: number;
  path: string;
  url: string;
};

export type Box = {
  x: number;
  y: number;
  w: number;
  h: number;
};

export type OverlayStyle = {
  font_size: number;
  font_weight: string;
  text_color: string;
  background_color: string;
  background_opacity: number;
  padding: number;
  radius: number;
  align: 'left' | 'center' | 'right';
};

export type TextSegment = {
  id: string;
  start_time: number;
  end_time: number;
  source_text: string;
  translated_text: string;
  box: Box;
  style: OverlayStyle;
  locked: boolean;
  confidence?: number | null;
};

export type ProjectState = {
  id: string;
  name: string;
  source_path: string;
  source_filename: string;
  created_at: string;
  updated_at: string;
  metadata?: VideoMetadata | null;
  frames: FrameAsset[];
  segments: TextSegment[];
  output_path?: string | null;
  output_url?: string | null;
  notes: string;
};

export type JobState = {
  id: string;
  kind: string;
  status: 'queued' | 'running' | 'done' | 'failed';
  progress: number;
  message: string;
  result?: { path: string; url: string } | null;
  error?: string | null;
};

export type Health = {
  ok: boolean;
  ocr: {
    available: boolean;
    engine: string;
  };
};

