import math
import re
from typing import List, Dict, Tuple

class SimpleVectorStore:
    def __init__(self, documents: List[Dict]):
        """
        In-memory vector store indexing day objects from curriculum.json.
        """
        self.documents = documents
        self.vocab: Dict[str, int] = {}
        self.doc_vectors: List[Dict[int, float]] = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase and extract alphanumeric tokens
        return re.findall(r'[a-zA-Z0-9_]+', text.lower())

    def _build_index(self):
        doc_term_freqs = []
        doc_counts = len(self.documents)
        df: Dict[str, int] = {}

        # 1. Count term frequencies across docs
        for doc in self.documents:
            text = f"{doc.get('title', '')} {doc.get('objectives', '')} {doc.get('content', '')}"
            tokens = self._tokenize(text)
            term_freq = {}
            for t in tokens:
                term_freq[t] = term_freq.get(t, 0) + 1
            doc_term_freqs.append(term_freq)
            
            for t in term_freq:
                df[t] = df.get(t, 0) + 1

        # 2. Map vocabulary to index ids
        vocab_idx = 0
        for token in df:
            self.vocab[token] = vocab_idx
            vocab_idx += 1

        # 3. Construct TF-IDF documents vectors with L2 normalization
        for i, term_freq in enumerate(doc_term_freqs):
            vector = {}
            length_sq = 0.0
            for term, count in term_freq.items():
                tf = count
                idf = math.log(1.0 + (doc_counts / (1.0 + df[term])))
                val = tf * idf
                vector[self.vocab[term]] = val
                length_sq += val * val
            
            length = math.sqrt(length_sq)
            if length > 0:
                for term_idx in vector:
                    vector[term_idx] /= length
            self.doc_vectors.append(vector)

    def search(self, query: str, top_k: int = 1) -> List[Tuple[Dict, float]]:
        """
        RAG vector search. Returns (document, similarity_score).
        """
        query_tokens = self._tokenize(query)
        query_term_freq = {}
        for t in query_tokens:
            if t in self.vocab:
                query_term_freq[t] = query_term_freq.get(t, 0) + 1

        query_vector = {}
        length_sq = 0.0
        for term, count in query_term_freq.items():
            term_idx = self.vocab[term]
            tf = count
            
            # IDF lookup smoothed
            vector_docs = [v.get(term_idx, 0.0) for v in self.doc_vectors]
            df_count = sum(1 for v in vector_docs if v > 0)
            idf = math.log(1.0 + (len(self.documents) / (1.0 + df_count)))
            val = tf * idf
            query_vector[term_idx] = val
            length_sq += val * val

        length = math.sqrt(length_sq)
        if length > 0:
            for term_idx in query_vector:
                query_vector[term_idx] /= length

        # Compute cosine similarity
        results = []
        for i, doc_vector in enumerate(self.doc_vectors):
            dot_product = 0.0
            for term_idx, query_val in query_vector.items():
                if term_idx in doc_vector:
                    dot_product += query_val * doc_vector[term_idx]
            results.append((self.documents[i], dot_product))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute similarity score between two arbitrary strings.
        Useful for 'recited vs explained' similarity detection.
        """
        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)
        
        freq_a = {}
        for t in tokens_a:
            freq_a[t] = freq_a.get(t, 0) + 1
            
        freq_b = {}
        for t in tokens_b:
            freq_b[t] = freq_b.get(t, 0) + 1
            
        # Combine vocabulary
        vocab = set(freq_a.keys()).union(set(freq_b.keys()))
        
        dot_product = 0.0
        len_a_sq = 0.0
        len_b_sq = 0.0
        
        for t in vocab:
            val_a = freq_a.get(t, 0)
            val_b = freq_b.get(t, 0)
            dot_product += val_a * val_b
            len_a_sq += val_a * val_a
            len_b_sq += val_b * val_b
            
        len_a = math.sqrt(len_a_sq)
        len_b = math.sqrt(len_b_sq)
        
        if len_a > 0 and len_b > 0:
            return dot_product / (len_a * len_b)
        return 0.0
