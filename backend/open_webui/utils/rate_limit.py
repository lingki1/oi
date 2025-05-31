import time
import math
from typing import Dict, List, Optional, Any
from open_webui.models.groups import Groups
from open_webui.utils.access_control import get_permissions


class GroupRateLimiter:
    """
    用户组频率限制器，基于滑动窗口算法限制用户组成员的模型使用频率
    """
    
    def __init__(self):
        # 存储用户请求历史: user_id -> List[timestamp]
        self.user_requests: Dict[str, List[float]] = {}
    
    def _get_user_rate_limit_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户的频率限制配置
        通过用户组权限系统获取rate_limit配置
        """
        try:
            # 获取用户的所有权限，包括频率限制配置
            default_permissions = {
                "rate_limit": {
                    "enabled": False,
                    "sliding_window_limit": 100,
                    "sliding_window_minutes": 15
                }
            }
            
            permissions = get_permissions(user_id, default_permissions)
            rate_limit_config = permissions.get("rate_limit", {})
            
            # 如果频率限制未启用，返回None
            if not rate_limit_config.get("enabled", False):
                return None
                
            return rate_limit_config
            
        except Exception as e:
            print(f"获取用户频率限制配置失败: {e}")
            return None
    
    def _prune_requests(self, user_id: str, window_minutes: int):
        """
        清理过期的请求记录，只保留在滑动窗口内的请求
        """
        if user_id not in self.user_requests:
            return
            
        now = time.time()
        window_seconds = window_minutes * 60
        
        # 只保留在滑动窗口内的请求
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < window_seconds
        ]
    
    def _log_request(self, user_id: str):
        """
        记录用户的请求时间戳
        """
        now = time.time()
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        self.user_requests[user_id].append(now)
        # 保持时间戳列表有序
        self.user_requests[user_id].sort()
    
    def _get_reset_time(self, user_id: str, config: Dict[str, Any]) -> Optional[float]:
        """
        检查用户是否达到频率限制，返回需要等待的秒数
        如果未达到限制，返回None
        """
        sliding_window_limit = config.get("sliding_window_limit", 100)
        sliding_window_minutes = config.get("sliding_window_minutes", 15)
        
        # 清理过期请求
        self._prune_requests(user_id, sliding_window_minutes)
        
        user_reqs = self.user_requests.get(user_id, [])
        now = time.time()
        window_seconds = sliding_window_minutes * 60
        
        # 检查滑动窗口内的请求数量
        requests_in_window = [
            req_time for req_time in user_reqs
            if now - req_time < window_seconds
        ]
        
        if len(requests_in_window) >= sliding_window_limit:
            # 计算需要等待的时间
            # 需要等待最早的请求过期
            idx_to_wait_for = len(requests_in_window) - sliding_window_limit
            if idx_to_wait_for >= 0:
                reset_timestamp = requests_in_window[idx_to_wait_for] + window_seconds
                return max(0, reset_timestamp - now)
        
        return None
    
    def check_rate_limit(self, user_id: str) -> Optional[str]:
        """
        检查用户是否达到频率限制
        
        Args:
            user_id: 用户ID
            
        Returns:
            如果达到限制，返回错误消息；否则返回None
        """
        try:
            # 获取用户的频率限制配置
            config = self._get_user_rate_limit_config(user_id)
            
            # 如果没有配置频率限制，直接通过
            if not config:
                return None
            
            # 检查是否达到限制
            reset_seconds = self._get_reset_time(user_id, config)
            
            if reset_seconds is not None:
                # 向上取整，给用户更保守的估计
                reset_seconds = math.ceil(reset_seconds)
                
                # 生成友好的等待时间消息
                if reset_seconds <= 0:
                    reset_message = "很快"
                elif reset_seconds < 60:
                    reset_message = f"{reset_seconds} 秒"
                elif reset_seconds < 3600:
                    reset_message = f"{int(reset_seconds / 60)} 分钟"
                else:
                    reset_message = f"{int(reset_seconds / 3600)} 小时"
                
                return f"抱歉，您的请求频率过高了。请稍等片刻，大约在 {reset_message} 后即可继续使用。感谢您的理解！"
            
            # 如果未达到限制，记录本次请求
            self._log_request(user_id)
            return None
            
        except Exception as e:
            print(f"频率限制检查失败: {e}")
            # 出现错误时，为了安全起见，不阻止请求
            return None


# 全局频率限制器实例
group_rate_limiter = GroupRateLimiter()