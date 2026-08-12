# 011 Video Text Replacement and Translation

> A desktop workflow that detects, translates, covers, and exports text embedded in video frames.

## Problem

Burned-in subtitles and on-screen text are hard to replace in batches, and translation can damage the original layout.

## Demo

~~~mermaid
flowchart LR
 A[Video] --> B[Text detection]
 B --> C[Translation]
 C --> D[Overlay and render]
 D --> E[Exported video]
~~~

The workflow keeps the video image while making text detection, translation, and rendering explicit.

## Highlights

- Desktop video-processing workflow.
- Chains OCR, translation, and overlay.
- Preserves the video image and exports a new file.
- The frontend/backend scripts are extendable.

## Tech

`Python · JavaScript · FFmpeg · OCR · Translation API · Node.js`

## Reproduce from ZIP

1. Extract the ZIP and install dependencies from `requirements.txt` and `package.json`.
2. Start the frontend/backend with the scripts in the project root.
3. Choose a test video, language, and output directory.
4. Review detected text, translations, and the exported video.

**Expected result:** After these steps, you should see the project's page, window, device output, or test result.

## Scope and Safety

The translation API and FFmpeg are runtime requirements; use your own test videos, API keys, and output directory.

## Contact

Open to technical exchange.
