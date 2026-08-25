# -*- coding: utf-8 -*-
"""Pydantic 数据模型（v2）"""
from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    behavior: str = Field(..., min_length=1,
                          description="员工行为自然语言描述（超长由服务端截断）")
    user_id: Optional[str] = Field(None, description="可选用户标识")


class StandardInfo(BaseModel):
    code: str = Field(..., description="准则代码，如 IV(B)")
    name: str = Field(..., description="准则中文名称")
    description: str = Field("", description="准则要求说明")


class ChecklistItem(BaseModel):
    id: int
    text: str
    required: bool = True


class ReferencedCase(BaseModel):
    question_id: str
    similarity: float
    risk_level: str = ""
    standard_code: List[str] = Field(default_factory=list)
    summary: str = ""


class AnalyzeResponse(BaseModel):
    risk_level: str = Field(..., description="high|mid|low")
    risk_score: float = Field(..., description="0-1 风险评分")
    category: str = Field("uncertain", description="行为类别")
    confidence: float = 0.0
    standards: List[StandardInfo] = Field(default_factory=list)
    checklist: List[ChecklistItem] = Field(default_factory=list)
    action_advice: str = ""
    disclosure_draft: str = ""
    risk_reasoning: str = ""
    referenced_cases: List[ReferencedCase] = Field(default_factory=list)
    processing_time_ms: int = 0
    offline: bool = Field(False, description="是否由本地规则引擎给出（未调用 LLM）")


class HealthResponse(BaseModel):
    status: str
    version: str
    corpus_size: int = 0
    embedding: str = "tfidf"


class SendDeclarationRequest(BaseModel):
    name: str = Field(..., description="申报人姓名")
    declaration_id: str = Field(..., description="申报编号")
    subject: str = Field(..., description="邮件主题")
    message: str = Field(..., description="邮件正文")


class SendDeclarationResponse(BaseModel):
    sent: bool
    message: str = ""


class PolishRequest(BaseModel):
    behavior: str = Field(..., min_length=1, description="口语化行为描述")


class PolishResponse(BaseModel):
    polished: str = Field(..., description="改写后的正式申报语言")


class SendApprovalRequest(BaseModel):
    declaration_id: str = Field(..., description="申报编号")
    name: str = Field(..., description="申报人姓名")
    behavior: str = Field(..., description="申报行为描述")
    result: str = Field(..., description="approved / rejected")
    signature: str = Field(..., description="审批人签名")
    opinion: str = Field("", description="审批意见（可选）")


class SendApprovalResponse(BaseModel):
    sent: bool
    message: str = ""
