import {
  Activity,
  CheckCircle2,
  Download,
  Film,
  FolderOpen,
  Layers3,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Scissors,
  Trash2,
  Upload,
} from 'lucide-react';
import { ChangeEvent, PointerEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from './api';
import type { Box, FrameAsset, Health, JobState, ProjectState, TextSegment } from './types';

const defaultStyle = {
  font_size: 34,
  font_weight: 'bold',
  text_color: '#ffffff',
  background_color: '#111111',
  background_opacity: 0.78,
  padding: 10,
  radius: 8,
  align: 'center' as const,
};

function createSegment(frame: FrameAsset | undefined, box: Box, duration: number): TextSegment {
  const start = Math.max(0, Math.floor(frame?.timestamp_sec ?? 0));
  const end = Math.min(duration || start + 5, Math.max(start + 1, start + 5));
  return {
    id: crypto.randomUUID(),
    start_time: start,
    end_time: end,
    source_text: '',
    translated_text: '翻译文字',
    box,
    style: defaultStyle,
    locked: false,
  };
}

function formatTime(value: number | undefined): string {
  if (!Number.isFinite(value ?? NaN)) return '00:00.0';
  const safe = Math.max(0, value ?? 0);
  const min = Math.floor(safe / 60);
  const sec = safe - min * 60;
  return `${String(min).padStart(2, '0')}:${sec.toFixed(1).padStart(4, '0')}`;
}

function clampBox(box: Box): Box {
  const x = Math.min(Math.max(box.x, 0), 0.98);
  const y = Math.min(Math.max(box.y, 0), 0.98);
  const w = Math.min(Math.max(box.w, 0.02), 1 - x);
  const h = Math.min(Math.max(box.h, 0.02), 1 - y);
  return { x, y, w, h };
}

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [projects, setProjects] = useState<ProjectState[]>([]);
  const [project, setProject] = useState<ProjectState | null>(null);
  const [selectedFrameId, setSelectedFrameId] = useState<string>('');
  const [selectedSegmentId, setSelectedSegmentId] = useState<string>('');
  const [pathInput, setPathInput] = useState('C:\\Users\\25021\\Documents\\WXWork\\1688856845869322\\Cache\\Video\\2026-07\\video.mp4');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [job, setJob] = useState<JobState | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const dragStartRef = useRef<{ x: number; y: number } | null>(null);
  const [draftBox, setDraftBox] = useState<Box | null>(null);

  const selectedFrame = useMemo(() => {
    if (!project?.frames.length) return undefined;
    return project.frames.find((frame) => frame.id === selectedFrameId) ?? project.frames[0];
  }, [project?.frames, selectedFrameId]);

  const selectedSegment = useMemo(() => {
    return project?.segments.find((segment) => segment.id === selectedSegmentId);
  }, [project?.segments, selectedSegmentId]);

  const load = useCallback(async () => {
    const [healthResult, projectList] = await Promise.all([api.health(), api.projects()]);
    setHealth(healthResult);
    setProjects(projectList);
    if (!project && projectList.length) {
      setProject(projectList[0]);
      setSelectedFrameId(projectList[0].frames[0]?.id ?? '');
    }
  }, [project]);

  useEffect(() => {
    load().catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, [load]);

  useEffect(() => {
    if (!job || job.status === 'done' || job.status === 'failed') return;
    const timer = window.setInterval(async () => {
      const next = await api.job(job.id);
      setJob(next);
      if (next.status === 'done' && project) {
        const refreshed = await api.projects();
        setProjects(refreshed);
        setProject(refreshed.find((item) => item.id === project.id) ?? project);
      }
    }, 900);
    return () => window.clearInterval(timer);
  }, [job, project]);

  async function run<T>(label: string, fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(label);
    setError('');
    try {
      return await fn();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return undefined;
    } finally {
      setBusy('');
    }
  }

  async function importByPath() {
    const result = await run('导入视频', () => api.importPath(pathInput));
    if (!result) return;
    setProject(result);
    setProjects((items) => [result, ...items.filter((item) => item.id !== result.id)]);
    const analyzed = await run('抽取预览帧', () => api.analyze(result.id, 8));
    if (analyzed) {
      setProject(analyzed);
      setSelectedFrameId(analyzed.frames[0]?.id ?? '');
      setProjects((items) => [analyzed, ...items.filter((item) => item.id !== analyzed.id)]);
    }
  }

  async function uploadFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const result = await run('上传视频', () => api.upload(file));
    if (!result) return;
    const analyzed = await run('抽取预览帧', () => api.analyze(result.id, 8));
    const next = analyzed ?? result;
    setProject(next);
    setSelectedFrameId(next.frames[0]?.id ?? '');
    setProjects((items) => [next, ...items.filter((item) => item.id !== next.id)]);
  }

  async function saveSegments(nextSegments = project?.segments ?? []) {
    if (!project) return;
    const result = await run('保存项目', () => api.saveSegments(project.id, nextSegments));
    if (!result) return;
    setProject(result);
    setProjects((items) => items.map((item) => (item.id === result.id ? result : item)));
  }

  async function render() {
    if (!project) return;
    const started = await run('提交导出', () => api.render(project.id, project.segments));
    if (started) setJob(started);
  }

  function updateSegment(segmentId: string, patch: Partial<TextSegment>) {
    if (!project) return;
    setProject({
      ...project,
      segments: project.segments.map((segment) => (
        segment.id === segmentId ? { ...segment, ...patch } : segment
      )),
    });
  }

  function addSegment(box?: Box) {
    if (!project) return;
    const next = createSegment(selectedFrame, box ?? { x: 0.12, y: 0.12, w: 0.42, h: 0.12 }, project.metadata?.duration_sec ?? 0);
    setProject({ ...project, segments: [...project.segments, next] });
    setSelectedSegmentId(next.id);
  }

  function removeSegment(segmentId: string) {
    if (!project) return;
    const next = project.segments.filter((segment) => segment.id !== segmentId);
    setProject({ ...project, segments: next });
    if (selectedSegmentId === segmentId) setSelectedSegmentId(next[0]?.id ?? '');
  }

  function pointerToBoxPoint(event: PointerEvent<HTMLDivElement>) {
    const stage = stageRef.current;
    if (!stage) return null;
    const rect = stage.getBoundingClientRect();
    return {
      x: Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)),
      y: Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height)),
    };
  }

  function onStagePointerDown(event: PointerEvent<HTMLDivElement>) {
    if (!project || !selectedFrame) return;
    if ((event.target as HTMLElement).dataset.segment) return;
    const point = pointerToBoxPoint(event);
    if (!point) return;
    dragStartRef.current = point;
    setDraftBox({ x: point.x, y: point.y, w: 0.01, h: 0.01 });
  }

  function onStagePointerMove(event: PointerEvent<HTMLDivElement>) {
    const start = dragStartRef.current;
    if (!start) return;
    const point = pointerToBoxPoint(event);
    if (!point) return;
    setDraftBox(clampBox({
      x: Math.min(start.x, point.x),
      y: Math.min(start.y, point.y),
      w: Math.abs(point.x - start.x),
      h: Math.abs(point.y - start.y),
    }));
  }

  function onStagePointerUp() {
    if (draftBox && draftBox.w > 0.02 && draftBox.h > 0.02) {
      addSegment(draftBox);
    }
    dragStartRef.current = null;
    setDraftBox(null);
  }

  const duration = project?.metadata?.duration_sec ?? 0;
  const frameUrl = selectedFrame ? `${selectedFrame.url}?t=${project?.updated_at ?? ''}` : '';
  const stageSegments = project?.segments.filter((segment) => {
    const t = selectedFrame?.timestamp_sec ?? 0;
    return segment.start_time <= t && segment.end_time >= t;
  }) ?? [];

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark"><Film size={20} /></div>
          <div>
            <h1>Video Text Translator</h1>
            <p>{health?.ocr.available ? `OCR ${health.ocr.engine}` : '手动校对模式'}</p>
          </div>
        </div>

        <section className="importPanel">
          <label className="fieldLabel">本地视频路径</label>
          <div className="pathRow">
            <input value={pathInput} onChange={(event) => setPathInput(event.target.value)} />
            <button className="iconButton primary" onClick={importByPath} title="导入路径">
              <FolderOpen size={18} />
            </button>
          </div>
          <label className="uploadButton">
            <Upload size={17} />
            <span>选择视频</span>
            <input type="file" accept="video/*" onChange={uploadFile} />
          </label>
        </section>

        <section className="projectList">
          <div className="sectionTitle">
            <span>项目</span>
            <button className="ghostIcon" onClick={() => load()} title="刷新"><RefreshCw size={16} /></button>
          </div>
          {projects.map((item) => (
            <button
              key={item.id}
              className={`projectItem ${project?.id === item.id ? 'active' : ''}`}
              onClick={() => {
                setProject(item);
                setSelectedFrameId(item.frames[0]?.id ?? '');
                setSelectedSegmentId(item.segments[0]?.id ?? '');
              }}
            >
              <span>{item.name}</span>
              <small>{item.metadata ? `${item.metadata.width}x${item.metadata.height} · ${formatTime(item.metadata.duration_sec)}` : '未分析'}</small>
            </button>
          ))}
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h2>{project?.name ?? '未选择项目'}</h2>
            <p>{project?.source_filename ?? '导入 MP4 后开始编辑'}</p>
          </div>
          <div className="topbarActions">
            <button className="secondaryButton" disabled={!project} onClick={() => project && api.analyze(project.id, 10).then(setProject)}><Activity size={17} />分析</button>
            <button className="secondaryButton" disabled={!project} onClick={() => saveSegments()}><Save size={17} />保存</button>
            <button className="primaryButton" disabled={!project || !project.segments.length} onClick={render}><Download size={17} />导出</button>
          </div>
        </header>

        {error && <div className="errorLine">{error}</div>}
        {busy && <div className="statusLine"><Loader2 className="spin" size={16} />{busy}</div>}

        <div className="mainGrid">
          <section className="stageColumn">
            <div className="stageHeader">
              <div>
                <strong>帧预览</strong>
                <span>{selectedFrame ? formatTime(selectedFrame.timestamp_sec) : '00:00.0'}</span>
              </div>
              <button className="secondaryButton compact" disabled={!project} onClick={() => addSegment()}><Plus size={16} />新增区域</button>
            </div>

            <div className="stageViewport">
              <div
                className="stage"
                style={{ aspectRatio: project?.metadata ? `${project.metadata.width} / ${project.metadata.height}` : '9 / 16' }}
                ref={stageRef}
                onPointerDown={onStagePointerDown}
                onPointerMove={onStagePointerMove}
                onPointerUp={onStagePointerUp}
              >
                {frameUrl ? <img src={frameUrl} alt="" draggable={false} /> : <div className="emptyStage"><Scissors size={34} /><span>等待视频帧</span></div>}
                {stageSegments.map((segment) => (
                  <button
                    key={segment.id}
                    data-segment="true"
                    className={`boxOverlay ${selectedSegmentId === segment.id ? 'selected' : ''}`}
                    style={{
                      left: `${segment.box.x * 100}%`,
                      top: `${segment.box.y * 100}%`,
                      width: `${segment.box.w * 100}%`,
                      height: `${segment.box.h * 100}%`,
                    }}
                    onClick={() => setSelectedSegmentId(segment.id)}
                  >
                    <span>{segment.translated_text}</span>
                  </button>
                ))}
                {draftBox && (
                  <div
                    className="boxOverlay drafting"
                    style={{
                      left: `${draftBox.x * 100}%`,
                      top: `${draftBox.y * 100}%`,
                      width: `${draftBox.w * 100}%`,
                      height: `${draftBox.h * 100}%`,
                    }}
                  />
                )}
              </div>
            </div>

            <div className="frameStrip">
              {project?.frames.map((frame) => (
                <button
                  key={frame.id}
                  className={selectedFrame?.id === frame.id ? 'active' : ''}
                  onClick={() => setSelectedFrameId(frame.id)}
                >
                  <img src={frame.url} alt="" />
                  <span>{formatTime(frame.timestamp_sec)}</span>
                </button>
              ))}
            </div>
          </section>

          <aside className="inspector">
            <div className="inspectorTitle">
              <Layers3 size={17} />
              <span>替换区域</span>
            </div>
            <div className="segments">
              {project?.segments.map((segment) => (
                <button
                  key={segment.id}
                  className={`segmentRow ${selectedSegmentId === segment.id ? 'active' : ''}`}
                  onClick={() => setSelectedSegmentId(segment.id)}
                >
                  <span>{segment.translated_text || '未命名区域'}</span>
                  <small>{formatTime(segment.start_time)} - {formatTime(segment.end_time)}</small>
                </button>
              ))}
            </div>

            {selectedSegment ? (
              <div className="editor">
                <label>原文</label>
                <input
                  value={selectedSegment.source_text}
                  onChange={(event) => updateSegment(selectedSegment.id, { source_text: event.target.value })}
                />
                <label>中文</label>
                <textarea
                  value={selectedSegment.translated_text}
                  onChange={(event) => updateSegment(selectedSegment.id, { translated_text: event.target.value })}
                />
                <div className="twoCols">
                  <label>开始<input type="number" step="0.1" value={selectedSegment.start_time} onChange={(event) => updateSegment(selectedSegment.id, { start_time: Number(event.target.value) })} /></label>
                  <label>结束<input type="number" step="0.1" value={selectedSegment.end_time} onChange={(event) => updateSegment(selectedSegment.id, { end_time: Number(event.target.value) })} /></label>
                </div>
                <div className="twoCols">
                  <label>字号<input type="number" value={selectedSegment.style.font_size} onChange={(event) => updateSegment(selectedSegment.id, { style: { ...selectedSegment.style, font_size: Number(event.target.value) } })} /></label>
                  <label>透明度<input type="number" min="0" max="1" step="0.05" value={selectedSegment.style.background_opacity} onChange={(event) => updateSegment(selectedSegment.id, { style: { ...selectedSegment.style, background_opacity: Number(event.target.value) } })} /></label>
                </div>
                <div className="twoCols">
                  <label>文字色<input type="color" value={selectedSegment.style.text_color} onChange={(event) => updateSegment(selectedSegment.id, { style: { ...selectedSegment.style, text_color: event.target.value } })} /></label>
                  <label>底色<input type="color" value={selectedSegment.style.background_color} onChange={(event) => updateSegment(selectedSegment.id, { style: { ...selectedSegment.style, background_color: event.target.value } })} /></label>
                </div>
                <button className="dangerButton" onClick={() => removeSegment(selectedSegment.id)}><Trash2 size={16} />删除区域</button>
              </div>
            ) : (
              <div className="emptyInspector">暂无选中区域</div>
            )}

            {job && (
              <div className="jobPanel">
                <div>
                  {job.status === 'done' ? <CheckCircle2 size={18} /> : <Loader2 className={job.status === 'running' ? 'spin' : ''} size={18} />}
                  <strong>{job.message}</strong>
                </div>
                <progress value={job.progress} max={1} />
                {job.result?.path && <a href={job.result.url} target="_blank" rel="noreferrer">{job.result.path}</a>}
                {job.error && <pre>{job.error}</pre>}
              </div>
            )}
          </aside>
        </div>
      </section>
    </main>
  );
}
