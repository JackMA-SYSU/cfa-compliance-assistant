# -*- coding: utf-8 -*-
"""合规分析 API 路由"""
import logging
import time

from fastapi import APIRouter, Request, HTTPException

from models.schemas import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger("compliance")
router = APIRouter(prefix="/api", tags=["compliance"])

# 简单内存限流：{ip: [timestamps]}
_rate_bucket = {}


def _rate_limited(ip: str, limit: int, window: int = 60) -> bool:
    now = time.time()
    stamps = _rate_bucket.setdefault(ip, [])
    _rate_bucket[ip] = [t for t in stamps if now - t < window]
    if len(_rate_bucket[ip]) >= limit:
        return True
    _rate_bucket[ip].append(now)
    return False


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, request: Request):
    # 限流
    ip = request.client.host if request.client else "unknown"
    if _rate_limited(ip, 20):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    engine = request.app.state.engine
    behavior = req.behavior.strip()
    if len(behavior) > 4000:
        behavior = behavior[:4000]

    try:
        result = engine.analyze(behavior)
    except Exception as e:  # noqa: BLE001
        logger.exception("分析失败")
        raise HTTPException(status_code=500, detail=f"分析服务异常: {e}")

    return result
