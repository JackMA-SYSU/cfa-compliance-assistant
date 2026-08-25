# -*- coding: utf-8 -*-
"""合规分析 API 路由"""
import logging
import time

from fastapi import APIRouter, Request, HTTPException

import config
from models.schemas import (
    AnalyzeRequest, AnalyzeResponse, SendDeclarationRequest, SendDeclarationResponse,
    PolishRequest, PolishResponse, SendApprovalRequest, SendApprovalResponse,
)

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


def _send_mail(subject: str, body: str, to: str):
    """通过 SMTP 发送邮件（默认 QQ 邮箱）"""
    import smtplib
    from email.header import Header
    from email.mime.text import MIMEText

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = config.SMTP_FROM
    msg["To"] = to

    if config.SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
    else:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        server.starttls()
    server.login(config.SMTP_USER, config.SMTP_PASSWORD)
    server.sendmail(config.SMTP_FROM, [to], msg.as_string())
    server.quit()


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


@router.post("/send-declaration", response_model=SendDeclarationResponse)
async def send_declaration(req: SendDeclarationRequest, request: Request):
    """通过 SMTP 发送申报邮件（默认 QQ 邮箱，国内无需翻墙）"""
    ip = request.client.host if request.client else "unknown"
    if _rate_limited(ip, 20):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    if not config.SMTP_PASSWORD:
        raise HTTPException(status_code=500, detail="邮件服务未配置（缺少 SMTP_PASSWORD 授权码）")

    try:
        _send_mail(req.subject, req.message, config.EMAIL_TO)
    except Exception as e:  # noqa: BLE001
        logger.exception("SMTP 发送异常")
        raise HTTPException(status_code=502, detail=f"邮件发送失败: {e}")

    return SendDeclarationResponse(sent=True, message=f"邮件已发送至 {config.EMAIL_TO}")


@router.post("/send-approval", response_model=SendApprovalResponse)
async def send_approval(req: SendApprovalRequest, request: Request):
    """合规部审批后，向员工回发审批结果邮件（含签名）"""
    ip = request.client.host if request.client else "unknown"
    if _rate_limited(ip, 20):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    if not config.SMTP_PASSWORD:
        raise HTTPException(status_code=500, detail="邮件服务未配置（缺少 SMTP_PASSWORD 授权码）")

    result_text = "已通过" if req.result == "approved" else "已驳回"
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    subject = f"【审批结果】申报 {req.declaration_id} {result_text}"
    body = (
        f"申报人 {req.name}：\n\n"
        f"您提交的合规申报（编号 {req.declaration_id}）经合规部审批，结果为：{result_text}。\n\n"
        f"【申报内容】\n{req.behavior}\n\n"
        + (f"【审批意见】\n{req.opinion}\n\n" if req.opinion else "")
        + f"审批人签名：{req.signature}\n"
        f"审批时间：{now}\n\n"
        f"此致\n合规部"
    )

    try:
        _send_mail(subject, body, config.EMPLOYEE_EMAIL)
    except Exception as e:  # noqa: BLE001
        logger.exception("审批邮件发送异常")
        raise HTTPException(status_code=502, detail=f"邮件发送失败: {e}")

    return SendApprovalResponse(sent=True, message=f"审批邮件已发送至 {config.EMPLOYEE_EMAIL}")


_POLISH_RULES = [
    ("客户请我吃饭", "接受客户宴请"),
    ("客户请我", "接受客户邀请"),
    ("客户送我", "接受客户提供的"),
    ("客户给我一笔钱", "接受客户支付的一笔报酬"),
    ("客户给我奖金", "接受客户支付的奖金"),
    ("客户给我", "接受客户提供的"),
    ("给我一笔钱", "向我支付一笔报酬"),
    ("给我奖金", "向我支付奖金"),
    ("请客", "宴请招待"),
    ("吃饭", "宴请"),
    ("打高尔夫", "高尔夫活动"),
    ("报销", "费用报销"),
    ("送我", "向我提供"),
    ("带我", "安排我"),
    ("送我去", "安排我前往"),
    ("承担", "由对方承担"),
]


def _local_polish(text: str) -> str:
    t = text.strip().rstrip("。！!；;")
    for a, b in _POLISH_RULES:
        t = t.replace(a, b)
    if t.startswith("本人"):
        return t + "，特此申报。"
    return "本人" + t + "，特此申报。"


@router.post("/polish", response_model=PolishResponse)
async def polish(req: PolishRequest, request: Request):
    """将口语化行为描述改写为正式申报语言（优先 DeepSeek，本地规则兜底）"""
    ip = request.client.host if request.client else "unknown"
    if _rate_limited(ip, 20):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    text = req.behavior.strip()

    if config.LLM_API_KEY:
        from services.llm_client import LLMClient
        try:
            client = LLMClient()
            resp = client.chat_completion(
                [{"role": "user", "content": (
                    "请把下面这句员工的口语化行为描述，改写为适合合规申报的正式书面语言。"
                    "要求：用第一人称「本人」，客观陈述事实，不做合规判断，不超过80字，只输出改写后的句子：\n"
                    f"{text}"
                )}],
                json_mode=False,
            )
            polished = (resp.get("content") or "").strip()
            if polished:
                return PolishResponse(polished=polished)
        except Exception as e:  # noqa: BLE001
            logger.warning("DeepSeek 转写失败，回退本地规则: %s", e)

    return PolishResponse(polished=_local_polish(text))
