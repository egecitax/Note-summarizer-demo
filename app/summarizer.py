# app/summarizer.py
import os

USE_HF = os.getenv("USE_HF", "false").lower() == "true"
HF_MODEL = os.getenv("HF_MODEL", "sshleifer/tiny-distilbart-cnn-6-6")

_hf_pipe = None

def _init_hf():
    from transformers import pipeline
    # device=-1 CPU; tiny model hızlıdır.
    return pipeline("summarization", model=HF_MODEL, device=-1)

def summarize_local_rule(text: str) -> str:
    s = [x.strip() for x in text.replace("\n", " ").split(".") if x.strip()]
    return ". ".join(s[:2])[:400]

def summarize(text: str) -> str:
    global _hf_pipe
    if USE_HF:
        try:
            if _hf_pipe is None:
                _hf_pipe = _init_hf()
            out = _hf_pipe(text, max_length=60, min_length=10, do_sample=False)
            # pipeline çıktısı: [{"summary_text": "..."}]
            return out[0]["summary_text"].strip()
        except Exception:
            # Model yüklenemezse sessizce fallback
            pass
    return summarize_local_rule(text)
