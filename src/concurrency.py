import time
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AdaptiveConcurrencyController:
    """
    自适应并发控制器
    - 正常模式: 允许最大并发数 (MAX)
    - 安全模式: 遇到连续错误后，降级到最小并发数 (MIN)
    - 恢复机制: 冷却一定时间后，线性释放并发额度 (每分钟+1)
    """
    def __init__(self, max_concurrency: int = 20, min_concurrency: int = 5):
        self.max_concurrency = max_concurrency
        self.min_concurrency = min_concurrency
        
        # State
        self.current_active = 0
        self._lock = threading.Lock()
        
        # Error tracking
        self.is_safe_mode = False
        self.last_error_time: float = 0
        self.consecutive_errors = 0
        self.error_threshold = 2  # 连续多少次 API 错误触发熔断
        
        # Recovery settings
        self.cooldown_seconds = 600  # 10分钟冷却
        self.recovery_rate_seconds = 60  # 每分钟恢复1个

    def get_dynamic_limit(self) -> int:
        """根据当前状态计算允许的最大并发数"""
        if not self.is_safe_mode:
            return self.max_concurrency
        
        elapsed = time.time() - self.last_error_time
        
        # 阶段1: 冷却期 (10分钟)
        if elapsed < self.cooldown_seconds:
            return self.min_concurrency
        
        # 阶段2: 线性恢复期
        recovery_time = elapsed - self.cooldown_seconds
        recovered_slots = int(recovery_time / self.recovery_rate_seconds)
        
        current_limit = self.min_concurrency + recovered_slots
        
        # 如果恢复到了最大值，退出安全模式
        if current_limit >= self.max_concurrency:
            with self._lock:
                self.is_safe_mode = False
                self.consecutive_errors = 0
                logger.info("系统已从安全模式完全恢复，并发限制解除。")
            return self.max_concurrency
            
        return current_limit

    def acquire(self):
        """
        阻塞直到获得执行许可。
        """
        while True:
            limit = self.get_dynamic_limit()
            with self._lock:
                if self.current_active < limit:
                    self.current_active += 1
                    return
            # 如果已满，稍微等待
            time.sleep(1)

    def release(self):
        with self._lock:
            self.current_active -= 1

    def report_error(self):
        """报告一次 API 错误，可能触发降级"""
        with self._lock:
            self.consecutive_errors += 1
            if not self.is_safe_mode and self.consecutive_errors >= self.error_threshold:
                self.is_safe_mode = True
                self.last_error_time = time.time()
                logger.warning(f"检测到连续 API 错误，系统进入[安全模式]。并发数降级为 {self.min_concurrency}，将冷却 {self.cooldown_seconds}秒。")

    def report_success(self):
        """报告一次成功，重置连续错误计数"""
        if self.consecutive_errors > 0:
            with self._lock:
                self.consecutive_errors = 0

# Global instance
concurrency_controller = None

def init_controller(max_c: int):
    global concurrency_controller
    concurrency_controller = AdaptiveConcurrencyController(max_concurrency=max_c)
