import type { Health, JobState, ProjectState, TextSegment } from './types';

const API_BASE = window.location.protocol === 'file:' ? 'http://127.0.0.1:8791' : '';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>('/api/health'),
  projects: () => request<ProjectState[]>('/api/projects'),
  importPath: (path: string) => request<ProjectState>('/api/projects/import-path', {
    method: 'POST',
    body: JSON.stringify({ path }),
  }),
  upload: (file: File) => {
    const body = new FormData();
    body.append('file', file);
    return request<ProjectState>('/api/projects/upload', { method: 'POST', body });
  },
  analyze: (projectId: string, sampleCount = 8) => request<ProjectState>(`/api/projects/${projectId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ sample_count: sampleCount }),
  }),
  saveSegments: (projectId: string, segments: TextSegment[]) => request<ProjectState>(`/api/projects/${projectId}/segments`, {
    method: 'PUT',
    body: JSON.stringify({ segments }),
  }),
  render: (projectId: string, segments: TextSegment[]) => request<JobState>(`/api/projects/${projectId}/render`, {
    method: 'POST',
    body: JSON.stringify({ segments }),
  }),
  job: (jobId: string) => request<JobState>(`/api/jobs/${jobId}`),
};
