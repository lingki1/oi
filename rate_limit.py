import os
from typing import List, Optional
from pydantic import BaseModel
from schemas import OpenAIChatMessage
import time
import math # 导入 math 模块用于向上取整

class Pipeline:
    class Valves(BaseModel):
        # List target pipeline ids (models) that this filter will be connected to.
        # If you want to connect this filter to all pipelines, you can set pipelines to ["*"]
        pipelines: List[str] = []
        # Assign a priority level to the filter pipeline.
        # The priority level determines the order in which the filter pipelines are executed.
        # The lower the number, the higher the priority.
        priority: int = 0
        # Valves for rate limiting
        target_user_roles: List[str] = ["user"]
        requests_per_minute: Optional[int] = None
        requests_per_hour: Optional[int] = None
        sliding_window_limit: Optional[int] = None
        sliding_window_minutes: Optional[int] = None

    def __init__(self):
        self.type = "filter"
        self.name = "Rate Limit Filter"
        self.valves = self.Valves(
            **{
                "pipelines": os.getenv("RATE_LIMIT_PIPELINES", "*").split(","),
                "target_user_roles": os.getenv("RATE_LIMIT_TARGET_USER_ROLES", "user").split(","),
                "requests_per_minute": int(
                    os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", 10)
                ),
                "requests_per_hour": int(
                    os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", 1000)
                ),
                "sliding_window_limit": int(
                    os.getenv("RATE_LIMIT_SLIDING_WINDOW_LIMIT", 100)
                ),
                "sliding_window_minutes": int(
                    os.getenv("RATE_LIMIT_SLIDING_WINDOW_MINUTES", 15)
                ),
            }
        )
        # Tracking data - user_id -> List[timestamps of requests]
        self.user_requests = {}

    async def on_startup(self):
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        pass

    def prune_requests(self, user_id: str):
        """修剪过期的请求，使其只保留在活跃限流窗口内的请求。"""
        now = time.time()
        if user_id in self.user_requests:
            # 仅保留在任何一个活跃窗口内的请求，避免列表无限增长
            self.user_requests[user_id] = [
                req
                for req in self.user_requests[user_id]
                if (
                    (self.valves.requests_per_minute is not None and now - req < 60)
                    or (self.valves.requests_per_hour is not None and now - req < 3600)
                    or (
                        self.valves.sliding_window_limit is not None
                        and self.valves.sliding_window_minutes is not None
                        and now - req < self.valves.sliding_window_minutes * 60
                    )
                )
            ]

    def log_request(self, user_id: str):
        """记录用户的最新请求时间戳。"""
        now = time.time()
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        self.user_requests[user_id].append(now)
        # 确保请求时间戳列表始终保持排序，方便计算最早过期时间
        self.user_requests[user_id].sort()

    def get_reset_time(self, user_id: str) -> Optional[float]:
        """
        检查用户是否达到限流，并返回需要等待的秒数。
        如果未限流，则返回 None；否则返回等待秒数。
        """
        self.prune_requests(user_id) # 确保数据是最新的
        user_reqs = self.user_requests.get(user_id, [])
        now = time.time()
        
        reset_times = [] # 存储所有触发限流的最小重置时间

        # 检查每分钟请求数限制
        if self.valves.requests_per_minute is not None and self.valves.requests_per_minute > 0:
            requests_last_minute = [req for req in user_reqs if now - req < 60]
            if len(requests_last_minute) >= self.valves.requests_per_minute:
                # 计算需要等待哪个请求过期才能释放一个槽位
                # 这是当前窗口内需要过期的第 (当前数量 - 限制数量) 个最早的请求
                # 假设列表已排序，索引为 len(requests_last_minute) - self.valves.requests_per_minute
                idx_to_wait_for = len(requests_last_minute) - self.valves.requests_per_minute
                if idx_to_wait_for >= 0: # 确保索引有效
                    reset_timestamp = requests_last_minute[idx_to_wait_for] + 60
                    reset_times.append(max(0, reset_timestamp - now))

        # 检查每小时请求数限制
        if self.valves.requests_per_hour is not None and self.valves.requests_per_hour > 0:
            requests_last_hour = [req for req in user_reqs if now - req < 3600]
            if len(requests_last_hour) >= self.valves.requests_per_hour:
                idx_to_wait_for = len(requests_last_hour) - self.valves.requests_per_hour
                if idx_to_wait_for >= 0:
                    reset_timestamp = requests_last_hour[idx_to_wait_for] + 3600
                    reset_times.append(max(0, reset_timestamp - now))

        # 检查滑动窗口限制
        if self.valves.sliding_window_limit is not None and self.valves.sliding_window_limit > 0 \
           and self.valves.sliding_window_minutes is not None:
            # 再次过滤，确保只考虑当前滑动窗口内的请求
            requests_in_sliding_window = [
                req for req in user_reqs if now - req < self.valves.sliding_window_minutes * 60
            ]
            
            if len(requests_in_sliding_window) >= self.valves.sliding_window_limit:
                idx_to_wait_for = len(requests_in_sliding_window) - self.valves.sliding_window_limit
                if idx_to_wait_for >= 0:
                    reset_timestamp = requests_in_sliding_window[idx_to_wait_for] + self.valves.sliding_window_minutes * 60
                    reset_times.append(max(0, reset_timestamp - now))

        if reset_times:
            # 返回所有触发限流条件中，最早可以继续发送请求的时间
            return min(reset_times)
        return None # 未达到任何限流

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"pipe:{__name__}")
        print(body)
        print(user)
        
        # 仅对配置的 target_user_roles 角色的用户应用限流
        if user and user.get("role") in self.valves.target_user_roles:
            user_id = user.get("id", "default_user") # 使用 .get() 更健壮地获取用户 ID
            
            reset_seconds = self.get_reset_time(user_id)
            
            if reset_seconds is not None:
                # 对等待时间向上取整，给用户一个更保守的估计
                reset_seconds = math.ceil(reset_seconds) 
                
                reset_message = ""
                if reset_seconds <= 0: # 理论上不应发生，但作为安全措施
                    reset_message = "很快"
                elif reset_seconds < 60:
                    reset_message = f"{reset_seconds} 秒"
                elif reset_seconds < 3600:
                    reset_message = f"{int(reset_seconds / 60)} 分钟"
                else:
                    reset_message = f"{int(reset_seconds / 3600)} 小时"
                
                # 抛出更温柔且包含等待时间的异常信息
                raise Exception(f"抱歉，您的请求频率过高了。请稍等片刻，大约在 {reset_message} 后即可继续使用。感谢您的理解！")
            
            # 如果未达到限流，则记录本次请求
            self.log_request(user_id)
        
        return body
