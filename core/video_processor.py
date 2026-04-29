"""
Video Processor — FFmpeg audio extraction + Whisper + T5
Works with file paths (no full file loaded into RAM).
Optimized for speed: tiny Whisper + greedy decode + 2 beams.
"""
import os, logging, threading, warnings, hashlib, tempfile, subprocess
warnings.filterwarnings('ignore')
logger = logging.getLogger('core.security')

_tokenizer = _t5_model = _whisper_model = _device = _load_error = None
_lock = threading.Lock()


def load_model():
    global _tokenizer, _t5_model, _whisper_model, _device, _load_error
    with _lock:
        if _t5_model is not None or _load_error is not None:
            return
        try:
            import torch, whisper
            from transformers import T5Tokenizer, T5ForConditionalGeneration

            base_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.environ.get('VIDEO_MODEL_PATH', 'Prakshal2503/video-summarizer-model')

            # Check FFmpeg is installed
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                _load_error = (
                    "FFmpeg not found. Install:\n"
                    "  Windows: winget install --id Gyan.FFmpeg\n"
                    "  Linux  : sudo apt install ffmpeg\n"
                    "  Mac    : brew install ffmpeg"
                )
                logger.error(_load_error)
                return

            device = 'cuda' if torch.cuda.is_available() else 'cpu'

            _tokenizer = T5Tokenizer.from_pretrained(model_path)
            _t5_model  = T5ForConditionalGeneration.from_pretrained(model_path).to(device)
            _t5_model.eval()

            # torch.compile gives 20-30% speed boost on PyTorch 2.0+
            _t5_model = torch.compile(_t5_model) if hasattr(torch, 'compile') else _t5_model

            # tiny = 39M params (was small = 244M) — 4x faster
            _whisper_model = whisper.load_model('tiny').to(device)

            _device = device
            logger.info(f'Video processor loaded on {device}')

        except ImportError as e:
            _load_error = f"Missing dependency: {e}. Run: pip install openai-whisper ffmpeg-python"
            logger.error(_load_error)
        except Exception as e:
            _load_error = f"Video model load failed: {e}"
            logger.error(_load_error)


def _chunk_text(text, max_words=480):
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]


def _summarize_text(text, max_len=128, min_len=20):
    import torch
    summaries = []
    for chunk in _chunk_text(text):
        inputs = _tokenizer(
            'summarize: ' + chunk,
            return_tensors='pt',
            max_length=512,
            truncation=True
        ).to(_device)
        with torch.no_grad():
            out = _t5_model.generate(
                **inputs,
                max_new_tokens       = max_len,
                min_length           = min_len,
                num_beams            = 2,
                length_penalty       = 1.0,
                early_stopping       = True,
                no_repeat_ngram_size = 2,
            )
        summaries.append(_tokenizer.decode(out[0], skip_special_tokens=True))
    if len(summaries) > 1:
        return _summarize_text(' '.join(summaries), max_len=150, min_len=30)
    return summaries[0]


def _extract_audio_from_video(video_path: str, audio_path: str):
    """FFmpeg: extract mono 16kHz WAV. Streams on disk, no RAM."""
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        audio_path,
        '-y',
        '-loglevel', 'quiet'
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed: {r.stderr.decode('utf-8', errors='replace')}"
        )


def process_video_file(file_path: str, original_name: str) -> dict:
    """
    Extract audio → transcribe → summarize.
    Everything stays on disk, nothing loaded into RAM.
    """
    if _t5_model is None and _load_error is None:
        load_model()
    if _load_error:
        return {'success': False, 'error': _load_error}

    audio_tmp = None
    try:
        # Hash by streaming
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(65536), b''):
                sha256.update(block)
        file_hash = sha256.hexdigest()

        ext      = os.path.splitext(original_name)[1].lower()
        is_video = ext in ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv')

        if is_video:
            audio_tmp     = file_path + '_audio.wav'
            _extract_audio_from_video(file_path, audio_tmp)
            whisper_input = audio_tmp
        else:
            whisper_input = file_path

        # Whisper reads from disk — greedy decode for speed
        result = _whisper_model.transcribe(
            whisper_input,
            fp16                       = (_device == 'cuda'),
            language                   = 'en',
            task                       = 'transcribe',
            condition_on_previous_text = False,
            temperature                = 0,
            best_of                    = 1,
            beam_size                  = 1,
            compression_ratio_threshold= 2.0,
        )
        transcript = result['text'].strip()

        if len(transcript.split()) < 5:
            return {
                'success': False,
                'error': f'Not enough speech detected. Got: "{transcript}"'
            }

        summary     = _summarize_text(transcript)
        word_count  = len(transcript.split())
        compression = f"{100 - (len(summary.split()) / max(word_count, 1) * 100):.0f}%"

        return {
            'success':     True,
            'transcript':  transcript,
            'summary':     summary,
            'word_count':  word_count,
            'compression': compression,
            'file_hash':   file_hash,
        }

    except Exception as e:
        logger.error(f'Video processing error: {e}')
        return {'success': False, 'error': str(e)}

    finally:
        if audio_tmp and os.path.exists(audio_tmp):
            try:
                os.unlink(audio_tmp)
            except Exception:
                pass


def summarize_text_with_model(text: str, model: str = 'video') -> str:
    """
    Summarize plain text using the loaded video T5 model.
    Called when user uploads a text/document file instead of video.
    """
    if _t5_model is None and _load_error is None:
        load_model()
    if _load_error:
        return f'[Model unavailable] {_load_error}'
    try:
        return _summarize_text(text)
    except Exception as e:
        logger.error(f'Text summarization error: {e}')
        return f'[Summarization error] {e}'


# Legacy bytes-based API
def process_video(file_bytes: bytes, filename: str) -> dict:
    ext = os.path.splitext(filename)[1].lower() or '.mp4'
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        return process_video_file(tmp_path, filename)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass