"""
T5 Dialogue Summarizer — model loader and inference.

This module loads the fine-tuned T5 model once at Django startup
(via apps.py ready()) and exposes a single function: summarize(text).

Model files must be placed at:
    <project_root>/best_model/
        config.json
        generation_config.json
        tokenizer.json
        tokenizer_config.json
        model.safetensors   (or pytorch_model.bin)

Set the environment variable MODEL_PATH to override the default location.
"""

import os
import logging
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger('core.security')

# ── Lazy globals — populated by load_model() ─────────────────────────────────
_tokenizer = None
_model = None
_device = None
_load_error = None   # stores error string if loading failed


def load_model():
    """
    Load tokenizer + model into module-level globals.
    Called once from CoreConfig.ready() in apps.py so the model
    is warm before the first request arrives.
    Silently records any error — summarize() returns a friendly
    message instead of crashing the server.
    """
    global _tokenizer, _model, _device, _load_error

    if _model is not None:
        return   # already loaded

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

        # Resolve model path — env var overrides the default
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.environ.get('MODEL_PATH', os.path.join(base_dir, 'best_model'))

        if not os.path.isdir(model_path):
            _load_error = (
                f"Model directory not found: '{model_path}'. "
                "Place your fine-tuned T5 files inside a folder called 'best_model' "
                "next to manage.py, or set the MODEL_PATH environment variable."
            )
            logger.warning(_load_error)
            return

        logger.info(f"Loading T5 model from {model_path} ...")
        _device = 'cuda' if torch.cuda.is_available() else 'cpu'
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        _model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(_device)
        _model.eval()
        logger.info(f"T5 model loaded on {_device}.")

    except ImportError as e:
        _load_error = (
            f"Missing dependency: {e}. "
            "Run: pip install torch transformers sentencepiece"
        )
        logger.error(_load_error)
    except Exception as e:
        _load_error = f"Model loading failed: {e}"
        logger.error(_load_error)


def summarize(text: str, max_len: int = 128, min_len: int = 20) -> str:
    """
    Summarize text using the loaded T5 model.

    Args:
        text:    Raw input text (dialogue or document content).
        max_len: Maximum number of new tokens to generate.
        min_len: Minimum number of tokens in the output.

    Returns:
        Summary string.  If the model is not loaded, returns a
        descriptive error message instead of raising an exception.
    """
    if _model is None:
        if _load_error:
            return f"[Model not available] {_load_error}"
        # Model not loaded yet — try lazy load
        load_model()
        if _model is None:
            return f"[Model not available] {_load_error or 'Unknown error during model load.'}"

    try:
        import torch

        # T5 was trained with a "summarize: " prefix
        inputs = _tokenizer(
            'summarize: ' + text,
            return_tensors='pt',
            max_length=512,
            truncation=True,
        ).to(_device)

        with torch.no_grad():
            outputs = _model.generate(
                **inputs,
                max_new_tokens=max_len,
                min_length=min_len,
                num_beams=4,
                length_penalty=2.0,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )

        return _tokenizer.decode(outputs[0], skip_special_tokens=True)

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return f"[Summarization error] {e}"
