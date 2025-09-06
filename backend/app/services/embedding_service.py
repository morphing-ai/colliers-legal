"""
Embedding Service for semantic similarity search
Uses OpenAI/Azure OpenAI for generating embeddings
"""
import logging
from typing import List, Optional
import numpy as np
from openai import AsyncAzureOpenAI, AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings."""
    
    def __init__(self):
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimension = 1536
        
        # Initialize client based on provider
        if settings.LLM_PROVIDER == "azure_openai":
            self.client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            # Azure uses deployment name instead of model
            self.embedding_model = "text-embedding-3-small"  # Update with your deployment name
        else:
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            )
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text string."""
        try:
            # Clean the text
            text = text.replace("\n", " ").strip()
            
            if not text:
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.embedding_dimension
            
            # Generate embedding
            response = await self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector on error
            return [0.0] * self.embedding_dimension
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch."""
        try:
            # Clean texts
            texts = [text.replace("\n", " ").strip() for text in texts]
            texts = [text if text else "empty" for text in texts]  # Handle empty strings
            
            # Generate embeddings in batch (OpenAI supports up to 2048 inputs)
            response = await self.client.embeddings.create(
                input=texts,
                model=self.embedding_model
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings in batch")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            # Return zero vectors on error
            return [[0.0] * self.embedding_dimension for _ in texts]
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        threshold: float = 0.0,
        top_k: Optional[int] = None
    ) -> List[tuple]:
        """
        Find most similar embeddings from candidates.
        Returns list of (index, similarity_score) tuples.
        """
        similarities = []
        
        for idx, candidate in enumerate(candidate_embeddings):
            similarity = self.cosine_similarity(query_embedding, candidate)
            if similarity >= threshold:
                similarities.append((idx, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k if specified
        if top_k:
            return similarities[:top_k]
        
        return similarities
    
    async def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text for better embedding."""
        # This is a simple implementation
        # Could be enhanced with NLP libraries or LLM extraction
        
        # Split into sentences
        sentences = text.split('.')
        
        # Filter out very short sentences
        key_phrases = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Limit to most important phrases (could use LLM to rank)
        return key_phrases[:5]
    
    def cluster_embeddings(
        self,
        embeddings: List[List[float]],
        num_clusters: int = 5
    ) -> Dict[int, List[int]]:
        """
        Cluster embeddings into groups.
        Returns dict mapping cluster_id to list of embedding indices.
        """
        try:
            from sklearn.cluster import KMeans
            
            # Convert to numpy array
            X = np.array(embeddings)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=min(num_clusters, len(embeddings)))
            labels = kmeans.fit_predict(X)
            
            # Group by cluster
            clusters = {}
            for idx, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(idx)
            
            return clusters
            
        except ImportError:
            logger.warning("scikit-learn not installed, clustering unavailable")
            return {0: list(range(len(embeddings)))}
        except Exception as e:
            logger.error(f"Error clustering embeddings: {str(e)}")
            return {0: list(range(len(embeddings)))}


# Global instance
embedding_service = EmbeddingService()