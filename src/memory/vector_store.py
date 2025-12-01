"""
向量数据库实现
支持 FAISS（本地）和 Milvus（可选）
"""

from typing import List, Dict, Optional
import os
import json
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

from langchain_openai import OpenAIEmbeddings


class VectorStore:
    """向量存储管理器"""
    
    def __init__(
        self,
        store_type: str = "faiss",
        embedding_model: str = "text-embedding-ada-002",
        api_key: Optional[str] = None,
        milvus_host: str = "localhost",
        milvus_port: int = 19530,
        collection_name: str = "werewolf_memory"
    ):
        """
        初始化向量存储
        
        Args:
            store_type: 存储类型 ("faiss" 或 "milvus")
            embedding_model: 嵌入模型名称
            api_key: API Key（用于 OpenAI embeddings）
            milvus_host: Milvus 主机地址
            milvus_port: Milvus 端口
            collection_name: Milvus 集合名称
        """
        self.store_type = store_type
        self.embedding_model = embedding_model
        
        # 初始化嵌入模型
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=api_key
        )
        
        if store_type == "faiss":
            if not FAISS_AVAILABLE:
                raise ImportError("FAISS not available. Install with: pip install faiss-cpu")
            self._init_faiss()
        elif store_type == "milvus":
            if not MILVUS_AVAILABLE:
                raise ImportError("Milvus not available. Install with: pip install pymilvus")
            self._init_milvus(milvus_host, milvus_port, collection_name)
        else:
            raise ValueError(f"Unsupported store_type: {store_type}")
        
        # 存储元数据
        self.metadata_store: List[Dict] = []
    
    def _init_faiss(self):
        """初始化 FAISS 索引"""
        self.dimension = 1536  # OpenAI embeddings 维度
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata_store = []
    
    def _init_milvus(self, host: str, port: int, collection_name: str):
        """初始化 Milvus 连接"""
        connections.connect("default", host=host, port=port)
        
        # 检查集合是否存在
        if utility.has_collection(collection_name):
            self.collection = Collection(collection_name)
        else:
            # 创建集合
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=10000),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=5000)
            ]
            schema = CollectionSchema(fields, "Werewolf game memory")
            self.collection = Collection(collection_name, schema)
        
        self.collection.load()
    
    def add_memory(self, text: str, metadata: Dict):
        """
        添加记忆
        
        Args:
            text: 文本内容
            metadata: 元数据（包含 player, round, phase 等）
        """
        # 生成嵌入
        embedding = self.embeddings.embed_query(text)
        embedding_array = np.array([embedding], dtype=np.float32)
        
        if self.store_type == "faiss":
            self.index.add(embedding_array)
            self.metadata_store.append({
                "text": text,
                "metadata": metadata
            })
        elif self.store_type == "milvus":
            data = [{
                "embedding": [embedding],
                "text": text,
                "metadata": json.dumps(metadata, ensure_ascii=False)
            }]
            self.collection.insert(data)
            self.collection.flush()
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.7) -> List[Dict]:
        """
        搜索相关记忆
        
        Args:
            query: 查询文本
            top_k: 返回前 K 条结果
            threshold: 相似度阈值
            
        Returns:
            相关记忆列表，包含 text 和 metadata
        """
        # 生成查询嵌入
        query_embedding = self.embeddings.embed_query(query)
        query_array = np.array([query_embedding], dtype=np.float32)
        
        if self.store_type == "faiss":
            # FAISS 搜索
            k = min(top_k, self.index.ntotal) if self.index.ntotal > 0 else 0
            if k == 0:
                return []
            
            distances, indices = self.index.search(query_array, k)
            
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.metadata_store):
                    # 计算相似度（L2距离转换为相似度）
                    similarity = 1 / (1 + distance)
                    if similarity >= threshold:
                        results.append({
                            "text": self.metadata_store[idx]["text"],
                            "metadata": self.metadata_store[idx]["metadata"],
                            "similarity": similarity
                        })
            
            return results
        
        elif self.store_type == "milvus":
            # Milvus 搜索
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "metadata"]
            )
            
            formatted_results = []
            for hits in results:
                for hit in hits:
                    similarity = 1 / (1 + hit.distance)
                    if similarity >= threshold:
                        formatted_results.append({
                            "text": hit.entity.get("text"),
                            "metadata": json.loads(hit.entity.get("metadata", "{}")),
                            "similarity": similarity
                        })
            
            return formatted_results
    
    def save(self, filepath: str):
        """保存 FAISS 索引到文件"""
        if self.store_type == "faiss":
            faiss.write_index(self.index, filepath)
            # 保存元数据
            metadata_file = filepath.replace(".index", "_metadata.json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata_store, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        """从文件加载 FAISS 索引"""
        if self.store_type == "faiss":
            self.index = faiss.read_index(filepath)
            # 加载元数据
            metadata_file = filepath.replace(".index", "_metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, "r", encoding="utf-8") as f:
                    self.metadata_store = json.load(f)

