import os
import re
from datetime import datetime
import psutil

# Optional PyNVML import for NVIDIA GPU tracking
try:
    import pynvml

    pynvml.nvmlInit()
    HAS_GPU_MONITOR = True
except Exception:
    HAS_GPU_MONITOR = False

# Persistent context log file path
CONTEXT_LOG_FILE = "context.txt"


def count_tokens(text: str) -> int:
    """Estimates token count using standard whitespace/word splitting."""
    if not text:
        return 0
    return len(re.findall(r"\w+|[^\w\s]", text))


def render_latex_for_terminal(text: str) -> str:
    """Cleans up raw LaTeX string markers and converts common math commands/fractions

    into clear, human-readable Unicode symbols for terminal display.
    """
    if not text:
        return ""

    cleaned = text

    # 1. Parse fractions: \frac{num}{den} -> num / (den)
    cleaned = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1 / (\2)", cleaned)

    # 2. Strip LaTeX wrapper delimiters & standalone trailing brackets
    cleaned = re.sub(r"\\\[|\\\]|\\\(|\\\)", "", cleaned)
    cleaned = (
        cleaned.replace("\]", "")
        .replace("\)", "")
        .replace("\[", "")
        .replace("\(", "")
    )

    # 3. Replace common LaTeX math commands with Unicode symbols
    replacements = {
        r"\cup": "∪",
        r"\cap": "∩",
        r"\infty": "∞",
        r"\pm": "±",
        r"\neq": "≠",
        r"\le": "≤",
        r"\ge": "≥",
        r"\times": "×",
        r"\div": "÷",
        r"\rightarrow": "→",
        r"\Rightarrow": "⇒",
        r"\leftarrow": "←",
        r"\Leftarrow": "⇐",
        r"\Leftrightarrow": "⇔",
        r"\in": "∈",
        r"\notin": "∉",
        r"\forall": "∀",
        r"\exists": "∃",
        r"\approx": "≈",
        r"\cdot": "·",
        r"\mathbb{R}": "ℝ",
        r"\mathbb{Z}": "ℤ",
        r"\mathbb{N}": "ℕ",
        r"\mathbb{Q}": "ℚ",
        r"\emptyset": "∅",
    }

    for latex, symbol in replacements.items():
        cleaned = cleaned.replace(latex, symbol)

    return cleaned


def get_system_metrics():
    """Returns current RAM and CPU usage strings."""
    try:
        ram = psutil.virtual_memory()
        ram_str = f"{ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB ({ram.percent}%)"
        cpu_str = f"{psutil.cpu_percent(interval=None)}%"
        return ram_str, cpu_str
    except Exception:
        return "N/A", "N/A"


def get_gpu_metrics():
    """Returns current NVIDIA GPU utilization and VRAM usage strings."""
    if not HAS_GPU_MONITOR:
        return "N/A", "N/A"
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

        gpu_util_str = f"{util.gpu}%"
        vram_str = f"{mem_info.used / (1024**2):.0f} MB / {mem_info.total / (1024**2):.0f} MB"
        return gpu_util_str, vram_str
    except Exception:
        return "N/A", "N/A"


def log_context_and_answer(question: str, top_chunk: str, llm_answer: str):
    """Appends to context.txt permanently without deleting previous session data."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chunk_text = (
        top_chunk.strip()
        if top_chunk and top_chunk.strip()
        else "[NO MATCHING CONTEXT FOUND IN VECTORSTORE]"
    )
    answer_text = (
        llm_answer.strip()
        if llm_answer and llm_answer.strip()
        else "[NO ANSWER GENERATED]"
    )

    log_entry = f"""================================================================================
TIMESTAMP : {timestamp}
QUESTION  : {question}
================================================================================
TOP BEST CHUNK:
--------------------------------------------------------------------------------
{chunk_text}

--------------------------------------------------------------------------------
LLM ANSWER:
--------------------------------------------------------------------------------
{answer_text}
================================================================================

"""
    # Using 'a' mode ensures it appends continuously across restarts
    try:
        with open(CONTEXT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
            f.flush()  # Force flushing memory buffer directly to disk
    except Exception as e:
        print(f"⚠️ Failed to append to context log: {e}")