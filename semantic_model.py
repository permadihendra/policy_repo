import gc
import os
import threading
import time

from sentence_transformers import SentenceTransformer


class SemanticModel:
    _model = None
    _last_used = None
    _lock = threading.Lock()
    _watcher_started = False

    @classmethod
    def get(cls):
        with cls._lock:
            cls._last_used = time.time()
            if cls._model is None:
                os.makedirs("cache", exist_ok=True)
                os.environ["HF_HOME"] = os.path.abspath("cache")
                os.environ["TORCH_HOME"] = os.path.abspath("cache")
                cls._model = SentenceTransformer(
                    "paraphrase-multilingual-mpnet-base-v2",
                    cache_folder=os.path.abspath("cache"),
                )
            if not cls._watcher_started:
                cls._start_watcher()
        return cls._model

    @classmethod
    def _start_watcher(cls):
        def monitor():
            while True:
                time.sleep(60)  # check every 60s
                with cls._lock:
                    if cls._model and cls._last_used:
                        inactive_for = time.time() - cls._last_used
                        if inactive_for > 300:  # 5 minutes
                            print("[semantic] Unloading model after inactivity")
                            del cls._model
                            cls._model = None
                            cls._last_used = None
                            gc.collect()

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        cls._watcher_started = True
