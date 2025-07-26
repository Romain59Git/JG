#!/usr/bin/env python3
"""
Local Memory Manager - ChromaDB Integration
100% Local vectorial memory with conversation persistence
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

from config import config


@dataclass
class ConversationEntry:
    """Single conversation entry with metadata"""
    id: str
    user_input: str
    ai_response: str
    timestamp: float
    response_time: float
    model_used: str
    tokens_used: int
    is_fallback: bool = False
    context_tags: List[str] = None
    
    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []


@dataclass
class MemoryEntry:
    """Memory entry for vectorial storage"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class LocalEmbeddingManager:
    """Local embedding generator using sentence-transformers"""
    
    def __init__(self):
        self.logger = logging.getLogger("EmbeddingManager")
        self.model = None
        self.model_name = config.memory.EMBEDDING_MODEL
        
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(self.model_name)
                self.logger.info(f"✅ Embedding model loaded: {self.model_name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load embedding model: {e}")
        else:
            self.logger.warning("⚠️ sentence-transformers not available")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self.model or not text.strip():
            return None
        
        try:
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"❌ Embedding generation failed: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            return [None] * len(texts)
        
        try:
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            self.logger.error(f"❌ Batch embedding generation failed: {e}")
            return [None] * len(texts)
    
    def is_available(self) -> bool:
        """Check if embedding model is available"""
        return self.model is not None


class ChromaDBManager:
    """Local ChromaDB vector database manager"""
    
    def __init__(self):
        self.logger = logging.getLogger("ChromaDBManager")
        self.client = None
        self.collection = None
        self.db_path = Path(config.memory.CHROMADB_PATH)
        
        if HAS_CHROMADB:
            try:
                self._initialize_db()
                self.logger.info("✅ ChromaDB initialized")
            except Exception as e:
                self.logger.error(f"❌ ChromaDB initialization failed: {e}")
        else:
            self.logger.warning("⚠️ ChromaDB not available")
    
    def _initialize_db(self):
        """Initialize ChromaDB client and collection"""
        # Ensure directory exists
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize client
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=config.memory.COLLECTION_NAME
            )
            self.logger.info(f"📂 Loaded existing collection: {config.memory.COLLECTION_NAME}")
        except ValueError:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=config.memory.COLLECTION_NAME,
                metadata={"description": "Jarvis conversation memory"}
            )
            self.logger.info(f"🆕 Created new collection: {config.memory.COLLECTION_NAME}")
    
    def add_entry(self, entry: MemoryEntry) -> bool:
        """Add memory entry to ChromaDB"""
        if not self.collection or not entry.embedding:
            return False
        
        try:
            self.collection.add(
                ids=[entry.id],
                embeddings=[entry.embedding],
                documents=[entry.content],
                metadatas=[entry.metadata]
            )
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to add entry to ChromaDB: {e}")
            return False
    
    def search_similar(
        self, 
        query_embedding: List[float], 
        limit: int = 5,
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """Search for similar entries"""
        if not self.collection:
            return []
        
        threshold = threshold or config.memory.SIMILARITY_THRESHOLD
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Filter by threshold and format results
            similar_entries = []
            for i, distance in enumerate(results['distances'][0]):
                if distance <= (1 - threshold):  # Convert similarity to distance
                    similar_entries.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': 1 - distance,
                        'distance': distance
                    })
            
            return similar_entries
            
        except Exception as e:
            self.logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self.collection:
            return {'error': 'Collection not available'}
        
        try:
            count = self.collection.count()
            return {
                'total_entries': count,
                'collection_name': config.memory.COLLECTION_NAME,
                'db_path': str(self.db_path)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_old_entries(self, days_to_keep: int = 30) -> int:
        """Clean up old entries"""
        if not self.collection:
            return 0
        
        try:
            # This is a simplified cleanup - ChromaDB doesn't have direct date filtering
            # In a real implementation, you'd need to implement this based on metadata
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            
            # For now, just return 0 as this requires more complex implementation
            self.logger.info(f"🧹 Cleanup requested for entries older than {days_to_keep} days")
            return 0
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup failed: {e}")
            return 0
    
    def is_available(self) -> bool:
        """Check if ChromaDB is available"""
        return self.collection is not None


class ConversationPersistence:
    """Local conversation persistence manager"""
    
    def __init__(self):
        self.logger = logging.getLogger("ConversationPersistence")
        self.conversations_dir = Path(config.memory.CONVERSATIONS_DIR)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session file
        self.current_session_file = self.conversations_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.conversation_buffer = []
        
        self.logger.info(f"📝 Conversation persistence initialized: {self.current_session_file}")
    
    def add_conversation(self, entry: ConversationEntry):
        """Add conversation entry to buffer"""
        self.conversation_buffer.append(asdict(entry))
        
        # Auto-save if buffer is full
        if len(self.conversation_buffer) >= config.memory.CONVERSATION_BATCH_SIZE:
            self.save_buffer()
    
    def save_buffer(self) -> bool:
        """Save conversation buffer to file"""
        if not self.conversation_buffer:
            return True
        
        try:
            # Load existing data if file exists
            existing_data = []
            if self.current_session_file.exists():
                with open(self.current_session_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Add new conversations
            existing_data.extend(self.conversation_buffer)
            
            # Save back to file
            with open(self.current_session_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Saved {len(self.conversation_buffer)} conversations")
            self.conversation_buffer.clear()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save conversations: {e}")
            return False
    
    def load_recent_conversations(self, limit: int = 50) -> List[ConversationEntry]:
        """Load recent conversations from files"""
        conversations = []
        
        try:
            # Get all session files, sorted by name (which includes timestamp)
            session_files = sorted(
                self.conversations_dir.glob("session_*.json"),
                reverse=True
            )
            
            for session_file in session_files:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    for entry_data in reversed(session_data):  # Most recent first
                        conversations.append(ConversationEntry(**entry_data))
                        
                        if len(conversations) >= limit:
                            break
                    
                    if len(conversations) >= limit:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to load session {session_file}: {e}")
                    continue
            
            self.logger.info(f"📚 Loaded {len(conversations)} recent conversations")
            return conversations
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load conversations: {e}")
            return []
    
    def get_conversation_history(self, hours: int = 24) -> List[ConversationEntry]:
        """Get conversation history for specified hours"""
        cutoff_time = time.time() - (hours * 3600)
        recent_conversations = self.load_recent_conversations(limit=200)
        
        # Filter by time
        filtered = [
            conv for conv in recent_conversations 
            if conv.timestamp >= cutoff_time
        ]
        
        return filtered
    
    def cleanup_old_files(self, days_to_keep: int = 7) -> int:
        """Clean up old conversation files"""
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        try:
            for session_file in self.conversations_dir.glob("session_*.json"):
                file_time = session_file.stat().st_mtime
                if file_time < cutoff_time:
                    session_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"🗑️ Deleted old session: {session_file.name}")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup failed: {e}")
            return 0


class MemoryManager:
    """Main local memory manager orchestrating all components"""
    
    def __init__(self):
        self.logger = logging.getLogger("MemoryManager")
        
        # Initialize components
        self.embedding_manager = LocalEmbeddingManager()
        self.chromadb_manager = ChromaDBManager()
        self.conversation_persistence = ConversationPersistence()
        
        # Memory statistics
        self.stats = {
            'conversations_stored': 0,
            'memories_created': 0,
            'searches_performed': 0,
            'embedding_failures': 0
        }
        
        self.logger.info("🧠 Memory Manager initialized")
    
    def store_conversation(
        self, 
        user_input: str, 
        ai_response: str,
        response_time: float = 0,
        model_used: str = "unknown",
        tokens_used: int = 0,
        is_fallback: bool = False,
        context_tags: List[str] = None
    ) -> bool:
        """Store a complete conversation exchange"""
        
        try:
            # Create conversation entry
            entry = ConversationEntry(
                id=str(uuid.uuid4()),
                user_input=user_input,
                ai_response=ai_response,
                timestamp=time.time(),
                response_time=response_time,
                model_used=model_used,
                tokens_used=tokens_used,
                is_fallback=is_fallback,
                context_tags=context_tags or []
            )
            
            # Store in conversation persistence
            if config.memory.SAVE_CONVERSATIONS:
                self.conversation_persistence.add_conversation(entry)
            
            # Create memory entry for vectorial search
            combined_content = f"User: {user_input}\nAssistant: {ai_response}"
            
            # Generate embedding if possible
            embedding = None
            if self.embedding_manager.is_available():
                embedding = self.embedding_manager.generate_embedding(combined_content)
                
                if not embedding:
                    self.stats['embedding_failures'] += 1
            
            # Store in ChromaDB if embedding available
            if embedding and self.chromadb_manager.is_available():
                memory_entry = MemoryEntry(
                    id=entry.id,
                    content=combined_content,
                    metadata={
                        'type': 'conversation',
                        'timestamp': entry.timestamp,
                        'model_used': model_used,
                        'is_fallback': is_fallback,
                        'response_time': response_time,
                        'tokens_used': tokens_used,
                        'tags': context_tags or []
                    },
                    embedding=embedding
                )
                
                self.chromadb_manager.add_entry(memory_entry)
                self.stats['memories_created'] += 1
            
            self.stats['conversations_stored'] += 1
            
            self.logger.debug(f"💾 Stored conversation: {user_input[:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store conversation: {e}")
            return False
    
    def search_relevant_memories(
        self, 
        query: str, 
        limit: int = None,
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories based on query"""
        
        limit = limit or config.memory.MAX_RELEVANT_MEMORIES
        threshold = threshold or config.memory.SIMILARITY_THRESHOLD
        
        if not self.embedding_manager.is_available() or not self.chromadb_manager.is_available():
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_manager.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Search in ChromaDB
            results = self.chromadb_manager.search_similar(
                query_embedding, 
                limit=limit,
                threshold=threshold
            )
            
            self.stats['searches_performed'] += 1
            
            self.logger.debug(f"🔍 Found {len(results)} relevant memories for: {query[:50]}...")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Memory search failed: {e}")
            return []
    
    def get_conversation_context(self, hours: int = 2) -> str:
        """Get formatted conversation context for AI"""
        
        try:
            recent_conversations = self.conversation_persistence.get_conversation_history(hours)
            
            if not recent_conversations:
                return ""
            
            # Format context
            context_lines = []
            context_lines.append(f"=== Recent Conversation Context ({len(recent_conversations)} exchanges) ===")
            
            for conv in recent_conversations[-10:]:  # Last 10 exchanges
                time_str = datetime.fromtimestamp(conv.timestamp).strftime("%H:%M")
                context_lines.append(f"[{time_str}] User: {conv.user_input}")
                context_lines.append(f"[{time_str}] Assistant: {conv.ai_response}")
            
            context_lines.append("=== End Context ===")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get conversation context: {e}")
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        
        stats = dict(self.stats)
        
        # Add component stats
        stats['embedding_available'] = self.embedding_manager.is_available()
        stats['chromadb_available'] = self.chromadb_manager.is_available()
        
        if self.chromadb_manager.is_available():
            chromadb_stats = self.chromadb_manager.get_stats()
            stats.update({f"chromadb_{k}": v for k, v in chromadb_stats.items()})
        
        return stats
    
    def cleanup_resources(self) -> Dict[str, int]:
        """Clean up old data and optimize storage"""
        
        cleanup_results = {
            'conversations_cleaned': 0,
            'memory_entries_cleaned': 0,
            'files_deleted': 0
        }
        
        try:
            # Clean old conversation files
            files_deleted = self.conversation_persistence.cleanup_old_files(days_to_keep=7)
            cleanup_results['files_deleted'] = files_deleted
            
            # Clean old ChromaDB entries (if implemented)
            memory_cleaned = self.chromadb_manager.cleanup_old_entries(days_to_keep=30)
            cleanup_results['memory_entries_cleaned'] = memory_cleaned
            
            # Save any pending conversations
            self.conversation_persistence.save_buffer()
            
            self.logger.info(f"🧹 Memory cleanup completed: {cleanup_results}")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup failed: {e}")
        
        return cleanup_results
    
    def is_fully_available(self) -> bool:
        """Check if all memory components are available"""
        return (self.embedding_manager.is_available() and 
                self.chromadb_manager.is_available())
    
    def get_health_status(self) -> Dict[str, str]:
        """Get health status of all components"""
        return {
            'embedding_manager': 'healthy' if self.embedding_manager.is_available() else 'unavailable',
            'chromadb_manager': 'healthy' if self.chromadb_manager.is_available() else 'unavailable',
            'conversation_persistence': 'healthy',  # File-based, always available
            'overall': 'healthy' if self.is_fully_available() else 'degraded'
        }


# Global instance
memory_manager = MemoryManager() 