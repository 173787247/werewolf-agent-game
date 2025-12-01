"""
成本追踪器
统计总调用 token 数、平均响应延迟、GPU 资源预估
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CallRecord:
    """API 调用记录"""
    timestamp: float
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency: float  # 响应延迟（秒）


class CostTracker:
    """成本追踪器"""
    
    def __init__(self):
        self.records: List[CallRecord] = []
        self.start_time: Optional[float] = None
    
    def record_call(
        self,
        model: str,
        tokens: int,
        prompt_tokens: int,
        completion_tokens: int,
        latency: Optional[float] = None
    ):
        """
        记录 API 调用
        
        Args:
            model: 模型名称
            tokens: 总 token 数
            prompt_tokens: Prompt token 数
            completion_tokens: Completion token 数
            latency: 响应延迟（秒）
        """
        if self.start_time is None:
            self.start_time = time.time()
        
        record = CallRecord(
            timestamp=time.time(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=tokens,
            latency=latency or 0.0
        )
        self.records.append(record)
    
    def get_total_tokens(self) -> int:
        """获取总 token 数"""
        return sum(r.total_tokens for r in self.records)
    
    def get_prompt_tokens(self) -> int:
        """获取总 prompt token 数"""
        return sum(r.prompt_tokens for r in self.records)
    
    def get_completion_tokens(self) -> int:
        """获取总 completion token 数"""
        return sum(r.completion_tokens for r in self.records)
    
    def get_average_latency(self) -> float:
        """获取平均响应延迟"""
        if not self.records:
            return 0.0
        
        latencies = [r.latency for r in self.records if r.latency > 0]
        if not latencies:
            return 0.0
        
        return sum(latencies) / len(latencies)
    
    def get_total_time(self) -> float:
        """获取总运行时间"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time
    
    def get_model_usage(self) -> Dict[str, Dict]:
        """获取各模型的使用统计"""
        model_stats = {}
        
        for record in self.records:
            if record.model not in model_stats:
                model_stats[record.model] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0
                }
            
            stats = model_stats[record.model]
            stats["calls"] += 1
            stats["total_tokens"] += record.total_tokens
            stats["prompt_tokens"] += record.prompt_tokens
            stats["completion_tokens"] += record.completion_tokens
        
        return model_stats
    
    def estimate_cost(self, price_per_1k_tokens: Dict[str, float]) -> Dict[str, float]:
        """
        估算成本（需要提供各模型的每 1K token 价格）
        
        Args:
            price_per_1k_tokens: {model: price_per_1k_tokens}
            
        Returns:
            各模型的成本估算
        """
        model_usage = self.get_model_usage()
        costs = {}
        
        for model, stats in model_usage.items():
            price = price_per_1k_tokens.get(model, 0.0)
            cost = (stats["total_tokens"] / 1000) * price
            costs[model] = cost
        
        return costs
    
    def estimate_gpu_resources(self) -> Dict[str, any]:
        """
        估算 GPU 资源需求（基于 token 数和模型）
        
        Returns:
            GPU 资源估算
        """
        # 简单的估算逻辑
        total_tokens = self.get_total_tokens()
        total_time = self.get_total_time()
        
        # 假设每个 token 需要一定的计算量
        # 这里使用简化的估算
        estimated_flops = total_tokens * 1000  # 假设每个 token 需要 1000 FLOPS
        
        return {
            "estimated_flops": estimated_flops,
            "total_time_seconds": total_time,
            "tokens_per_second": total_tokens / total_time if total_time > 0 else 0,
            "note": "这是基于 token 数的简化估算，实际 GPU 使用取决于模型大小和推理配置"
        }
    
    def get_summary(self) -> Dict:
        """获取成本统计摘要"""
        return {
            "total_calls": len(self.records),
            "total_tokens": self.get_total_tokens(),
            "prompt_tokens": self.get_prompt_tokens(),
            "completion_tokens": self.get_completion_tokens(),
            "average_latency": self.get_average_latency(),
            "total_time": self.get_total_time(),
            "model_usage": self.get_model_usage(),
            "gpu_estimate": self.estimate_gpu_resources()
        }
    
    def reset(self):
        """重置统计"""
        self.records = []
        self.start_time = None

