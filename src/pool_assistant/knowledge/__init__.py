"""The manual content: ingestion.py builds the passage index from the PDFs, base.py loads it
and searches it. Other modules only need these two names."""

from pool_assistant.knowledge.base import KnowledgeBase, load_knowledge_base

__all__ = ["KnowledgeBase", "load_knowledge_base"]
