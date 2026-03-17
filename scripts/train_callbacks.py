"""Training callbacks for CPU-optimized training."""

import time
from transformers import TrainerCallback


class MemoryMonitorCallback(TrainerCallback):
    """Pause training when RAM usage exceeds threshold to avoid freezing."""

    def __init__(self, threshold: float = 0.9, check_interval_steps: int = 10):
        self.threshold = threshold
        self.check_interval_steps = check_interval_steps
        self._step_count = 0

    def on_step_end(self, args, state, control, **kwargs):
        self._step_count += 1
        if self._step_count % self.check_interval_steps != 0:
            return control

        try:
            import psutil
            mem = psutil.virtual_memory()
            if mem.percent >= self.threshold * 100:
                print(f"\n[MemoryMonitor] RAM at {mem.percent:.1f}% - pausing 30s to allow GC...")
                time.sleep(30)
                import gc
                gc.collect()
        except ImportError:
            pass
        return control
