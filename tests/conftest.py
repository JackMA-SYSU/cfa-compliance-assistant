# -*- coding: utf-8 -*-
"""pytest 公共夹具"""
import os
import sys

import pytest

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


@pytest.fixture(scope="session")
def kb():
    from build_kb import EthicsKnowledgeBase
    return EthicsKnowledgeBase()


@pytest.fixture(scope="session")
def classifier(kb):
    from services.classifier import RuleBasedClassifier
    return RuleBasedClassifier(kb=kb)


@pytest.fixture(scope="session")
def engine(kb, classifier):
    from services.rag_engine import RAGEngine
    return RAGEngine(kb=kb, classifier=classifier)
