"""
RAG (Retrieval-Augmented Generation) indexing service for EduAnalytics.

Indexes Canvas content, course materials, and educational resources for AI-powered search and recommendations.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.page import Page
from app.models.discussion import Discussion
from app.models.quiz import Quiz

logger = logging.getLogger(__name__)


class Document:
    """Document representation for RAG indexing."""
    
    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None
    ):
        self.content = content
        self.metadata = metadata
        self.doc_id = doc_id or self._generate_id()
        self.embedding: Optional[np.ndarray] = None
        self.indexed_at = datetime.utcnow()
    
    def _generate_id(self) -> str:
        """Generate unique document ID from content and metadata."""
        content_hash = hashlib.md5(
            (self.content + json.dumps(self.metadata, sort_keys=True)).encode()
        ).hexdigest()
        return f"doc_{content_hash[:16]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for storage."""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "indexed_at": self.indexed_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create document from dictionary."""
        doc = cls(
            content=data["content"],
            metadata=data["metadata"],
            doc_id=data["doc_id"]
        )
        if data.get("embedding"):
            doc.embedding = np.array(data["embedding"])
        if data.get("indexed_at"):
            doc.indexed_at = datetime.fromisoformat(data["indexed_at"])
        return doc


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        self.model_name = getattr(settings, 'EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        self.model = None
        self.dimension = 384  # Default for MiniLM
        self._load_model()
    
    def _load_model(self):
        """Load embedding model."""
        try:
            # Try to use sentence-transformers
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded embedding model: {self.model_name} (dim: {self.dimension})")
        except Exception as e:
            logger.warning(f"Failed to load sentence-transformers model: {e}")
            # Fallback to simple TF-IDF or random embeddings for testing
            self._setup_fallback_embeddings()
    
    def _setup_fallback_embeddings(self):
        """Setup fallback embedding method."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.model = TfidfVectorizer(max_features=384, stop_words='english')
            self.dimension = 384
            logger.info("Using TF-IDF fallback embeddings")
        except Exception as e:
            logger.warning(f"TF-IDF fallback failed: {e}")
            # Use random embeddings as last resort
            self.model = None
            self.dimension = 384
            logger.warning("Using random embeddings (for testing only)")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        if not text or not text.strip():
            return np.zeros(self.dimension)
        
        try:
            if hasattr(self.model, 'encode'):
                # SentenceTransformer
                embedding = self.model.encode([text])[0]
                return np.array(embedding)
            elif hasattr(self.model, 'transform'):
                # TF-IDF
                embedding = self.model.transform([text]).toarray()[0]
                return embedding
            else:
                # Random fallback
                np.random.seed(hash(text) % 2**32)
                return np.random.normal(0, 1, self.dimension)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.dimension)
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        
        try:
            if hasattr(self.model, 'encode'):
                # SentenceTransformer batch encoding
                embeddings = self.model.encode(texts)
                return [np.array(emb) for emb in embeddings]
            else:
                # Fallback to individual encoding
                return [self.embed_text(text) for text in texts]
        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            return [self.embed_text(text) for text in texts]


class VectorStore:
    """Simple in-memory vector store for document embeddings."""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.embeddings: Optional[np.ndarray] = None
        self.doc_ids: List[str] = []
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the store."""
        for doc in documents:
            if doc.embedding is None:
                logger.warning(f"Document {doc.doc_id} has no embedding")
                continue
            
            self.documents[doc.doc_id] = doc
            if doc.doc_id not in self.doc_ids:
                self.doc_ids.append(doc.doc_id)
        
        # Rebuild embedding matrix
        self._rebuild_embeddings()
    
    def _rebuild_embeddings(self):
        """Rebuild the embedding matrix."""
        if not self.doc_ids:
            self.embeddings = None
            return
        
        embeddings = []
        for doc_id in self.doc_ids:
            doc = self.documents.get(doc_id)
            if doc and doc.embedding is not None:
                embeddings.append(doc.embedding)
        
        if embeddings:
            self.embeddings = np.vstack(embeddings)
        else:
            self.embeddings = None
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.embeddings is None or len(self.doc_ids) == 0:
            return []
        
        try:
            # Calculate cosine similarity
            query_norm = np.linalg.norm(query_embedding)
            if query_norm == 0:
                return []
            
            similarities = np.dot(self.embeddings, query_embedding) / (
                np.linalg.norm(self.embeddings, axis=1) * query_norm
            )
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if idx < len(self.doc_ids):
                    doc_id = self.doc_ids[idx]
                    doc = self.documents.get(doc_id)
                    if doc:
                        # Apply metadata filtering
                        if filter_metadata:
                            match = all(
                                doc.metadata.get(k) == v 
                                for k, v in filter_metadata.items()
                            )
                            if not match:
                                continue
                        
                        results.append({
                            "document": doc,
                            "score": float(similarities[idx]),
                            "doc_id": doc_id
                        })
            
            return results
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.documents.get(doc_id)
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove document from store."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            if doc_id in self.doc_ids:
                self.doc_ids.remove(doc_id)
            self._rebuild_embeddings()
            return True
        return False
    
    def clear(self):
        """Clear all documents."""
        self.documents.clear()
        self.doc_ids.clear()
        self.embeddings = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            "total_documents": len(self.documents),
            "embedding_dimension": self.embeddings.shape[1] if self.embeddings is not None else None,
            "memory_usage_mb": self.embeddings.nbytes / (1024 * 1024) if self.embeddings is not None else 0
        }


class RAGIndexer:
    """Main RAG indexing service."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.index_file = Path("rag_index.json")
        self.load_index()
    
    def save_index(self):
        """Save index to disk."""
        try:
            index_data = {
                "documents": {
                    doc_id: doc.to_dict() 
                    for doc_id, doc in self.vector_store.documents.items()
                },
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "total_documents": len(self.vector_store.documents),
                    "embedding_dimension": self.embedding_service.dimension
                }
            }
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved RAG index with {len(self.vector_store.documents)} documents")
        except Exception as e:
            logger.error(f"Failed to save RAG index: {e}")
    
    def load_index(self):
        """Load index from disk."""
        try:
            if not self.index_file.exists():
                logger.info("No existing RAG index found")
                return
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            documents = []
            for doc_data in index_data.get("documents", {}).values():
                doc = Document.from_dict(doc_data)
                documents.append(doc)
            
            self.vector_store.add_documents(documents)
            logger.info(f"Loaded RAG index with {len(documents)} documents")
        except Exception as e:
            logger.error(f"Failed to load RAG index: {e}")
    
    async def index_course_content(self, course_id: int, db: AsyncSession):
        """Index all content for a specific course."""
        try:
            logger.info(f"Starting to index course {course_id}")
            
            # Get course
            course_result = await db.execute(
                select(Course).where(Course.id == course_id)
            )
            course = course_result.scalar_one_or_none()
            if not course:
                logger.warning(f"Course {course_id} not found")
                return
            
            documents = []
            
            # Index course description
            if course.description:
                doc = Document(
                    content=f"{course.name}\n\n{course.description}",
                    metadata={
                        "type": "course",
                        "course_id": course.id,
                        "course_name": course.name,
                        "source": "course_description"
                    }
                )
                documents.append(doc)
            
            # Index assignments
            assignments_result = await db.execute(
                select(Assignment).where(Assignment.course_id == course_id)
            )
            assignments = assignments_result.scalars().all()
            
            for assignment in assignments:
                content = f"Assignment: {assignment.title}"
                if assignment.description:
                    content += f"\n\n{assignment.description}"
                
                doc = Document(
                    content=content,
                    metadata={
                        "type": "assignment",
                        "course_id": course.id,
                        "course_name": course.name,
                        "assignment_id": assignment.id,
                        "assignment_title": assignment.title,
                        "assignment_type": assignment.assignment_type,
                        "source": "assignment"
                    }
                )
                documents.append(doc)
            
            # Index pages
            pages_result = await db.execute(
                select(Page).where(Page.course_id == course_id)
            )
            pages = pages_result.scalars().all()
            
            for page in pages:
                content = f"Page: {page.title}"
                if page.body:
                    content += f"\n\n{page.body}"
                
                doc = Document(
                    content=content,
                    metadata={
                        "type": "page",
                        "course_id": course.id,
                        "course_name": course.name,
                        "page_id": page.id,
                        "page_title": page.title,
                        "source": "course_page"
                    }
                )
                documents.append(doc)
            
            # Index discussions
            discussions_result = await db.execute(
                select(Discussion).where(Discussion.course_id == course_id)
            )
            discussions = discussions_result.scalars().all()
            
            for discussion in discussions:
                content = f"Discussion: {discussion.title}"
                if discussion.message:
                    content += f"\n\n{discussion.message}"
                
                doc = Document(
                    content=content,
                    metadata={
                        "type": "discussion",
                        "course_id": course.id,
                        "course_name": course.name,
                        "discussion_id": discussion.id,
                        "discussion_title": discussion.title,
                        "source": "discussion"
                    }
                )
                documents.append(doc)
            
            # Index quizzes
            quizzes_result = await db.execute(
                select(Quiz).where(Quiz.course_id == course_id)
            )
            quizzes = quizzes_result.scalars().all()
            
            for quiz in quizzes:
                content = f"Quiz: {quiz.title}"
                if quiz.description:
                    content += f"\n\n{quiz.description}"
                
                doc = Document(
                    content=content,
                    metadata={
                        "type": "quiz",
                        "course_id": course.id,
                        "course_name": course.name,
                        "quiz_id": quiz.id,
                        "quiz_title": quiz.title,
                        "source": "quiz"
                    }
                )
                documents.append(doc)
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} documents")
            texts = [doc.content for doc in documents]
            embeddings = self.embedding_service.embed_batch(texts)
            
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
            
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            # Save index
            self.save_index()
            
            logger.info(f"Successfully indexed {len(documents)} documents for course {course_id}")
            
        except Exception as e:
            logger.error(f"Error indexing course {course_id}: {e}")
    
    async def index_all_courses(self):
        """Index content for all courses."""
        try:
            async with AsyncSessionLocal() as db:
                courses_result = await db.execute(select(Course))
                courses = courses_result.scalars().all()
                
                logger.info(f"Starting to index {len(courses)} courses")
                
                for course in courses:
                    await self.index_course_content(course.id, db)
                    # Small delay to prevent overwhelming the system
                    await asyncio.sleep(0.1)
                
                logger.info("Completed indexing all courses")
                
        except Exception as e:
            logger.error(f"Error indexing all courses: {e}")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        course_id: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant content."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            
            # Build metadata filter
            filter_metadata = {}
            if course_id:
                filter_metadata["course_id"] = course_id
            if content_type:
                filter_metadata["type"] = content_type
            
            # Search vector store
            results = self.vector_store.search(
                query_embedding, 
                top_k=top_k,
                filter_metadata=filter_metadata if filter_metadata else None
            )
            
            # Format results
            formatted_results = []
            for result in results:
                doc = result["document"]
                formatted_results.append({
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "score": result["score"],
                    "doc_id": result["doc_id"]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in RAG search: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        store_stats = self.vector_store.get_stats()
        
        # Count by content type
        type_counts = {}
        for doc in self.vector_store.documents.values():
            doc_type = doc.metadata.get("type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        return {
            **store_stats,
            "content_types": type_counts,
            "embedding_model": self.embedding_service.model_name,
            "index_file": str(self.index_file),
            "last_updated": datetime.utcnow().isoformat()
        }


# Global RAG indexer instance
rag_indexer = RAGIndexer()
