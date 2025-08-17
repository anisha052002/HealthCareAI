# app.py - Main Healthcare AI Assistant Application
# This is the simplified version for quick deployment

import os
import hashlib
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging
from datetime import datetime

# Core dependencies
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
import chromadb
from chromadb.utils import embedding_functions

# LangChain components
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import OpenAI
from langchain.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

# Document processing
import PyPDF2
import docx
import pandas as pd

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration settings for the healthcare assistant"""
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')
    UPLOAD_FOLDER: str = 'uploads'
    VECTOR_DB_PATH: str = 'healthcare_vectordb'
    MAX_FILE_SIZE: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: set = {'txt', 'pdf', 'docx', 'csv'}
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MEMORY_WINDOW: int = 10

class DocumentProcessor:
    """Handles document loading, processing, and chunking"""
    
    def __init__(self, config: Config):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.config.ALLOWED_EXTENSIONS
    
    def load_document(self, file_path: str) -> List[Document]:
        """Load document based on file type"""
        file_extension = file_path.rsplit('.', 1)[1].lower()
        
        try:
            if file_extension == 'pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension == 'docx':
                loader = Docx2txtLoader(file_path)
            elif file_extension == 'txt':
                loader = TextLoader(file_path)
            elif file_extension == 'csv':
                df = pd.read_csv(file_path)
                content = df.to_string(index=False)
                return [Document(page_content=content, metadata={"source": file_path})]
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks and add healthcare-specific metadata"""
        chunks = self.text_splitter.split_documents(documents)
        
        for chunk in chunks:
            chunk.metadata.update({
                'processed_at': datetime.now().isoformat(),
                'chunk_id': hashlib.md5(chunk.page_content.encode()).hexdigest()[:8],
                'domain': 'healthcare'
            })
        
        logger.info(f"Created {len(chunks)} chunks from documents")
        return chunks

class VectorDatabase:
    """Manages ChromaDB vector database operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config.OPENAI_API_KEY,
            model_name="text-embedding-ada-002"
        )
        self.client = chromadb.PersistentClient(path=config.VECTOR_DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name="healthcare_documents",
            embedding_function=self.embedding_function
        )
    
    def add_documents(self, chunks: List[Document]) -> None:
        """Add document chunks to vector database"""
        try:
            documents = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [chunk.metadata['chunk_id'] for chunk in chunks]
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector database")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector database: {str(e)}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': self.collection.name
        }

class HealthcareAIAssistant:
    """Main AI assistant class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.doc_processor = DocumentProcessor(config)
        self.vector_db = VectorDatabase(config)
        
        # Initialize LangChain components
        self.embeddings = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
        self.llm = OpenAI(
            temperature=0.1,
            openai_api_key=config.OPENAI_API_KEY,
            model_name="gpt-3.5-turbo-instruct"
        )
        
        # Memory for conversation
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=config.MEMORY_WINDOW
        )
        
        # Create LangChain vector store wrapper
        self._setup_retrieval_chain()
    
    def _setup_retrieval_chain(self):
        """Setup the retrieval chain for Q&A"""
        vectorstore = Chroma(
            persist_directory=self.config.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            memory=self.memory,
            return_source_documents=True,
            verbose=True
        )
    
    def upload_document(self, file_path: str) -> Dict[str, Any]:
        """Upload and process a new document"""
        try:
            documents = self.doc_processor.load_document(file_path)
            chunks = self.doc_processor.process_documents(documents)
            self.vector_db.add_documents(chunks)
            self._setup_retrieval_chain()
            
            return {
                'status': 'success',
                'message': f'Successfully processed document with {len(chunks)} chunks',
                'chunks_created': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Ask a question and get AI-powered answer"""
        try:
            enhanced_question = f"""
            As a healthcare knowledge assistant, please provide a comprehensive and accurate answer to the following question. 
            Base your response on the provided medical documents and healthcare knowledge.
            
            Question: {question}
            
            Please include:
            1. A clear, evidence-based answer
            2. Relevant citations from the source documents
            3. Any important caveats or limitations
            4. Suggestions for further consultation if needed
            
            Remember: This is for informational purposes only and should not replace professional medical advice.
            """
            
            result = self.qa_chain({"question": enhanced_question})
            
            sources = []
            for doc in result.get('source_documents', []):
                sources.append({
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'source': doc.metadata.get('source', 'Unknown'),
                    'page': doc.metadata.get('page', 'N/A')
                })
            
            return {
                'status': 'success',
                'answer': result['answer'],
                'sources': sources,
                'question': question
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'answer': 'I apologize, but I encountered an error while processing your question. Please try again.'
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        db_stats = self.vector_db.get_stats()
        return {
            'database': db_stats,
            'memory_messages': len(self.memory.chat_memory.messages),
            'status': 'active'
        }

# Flask Application
app = Flask(__name__)
app.secret_key = 'healthcare-ai-assistant-secret-key'

# Configuration
config = Config()
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE

# Create upload directory
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

# Initialize AI assistant
assistant = HealthcareAIAssistant(config)

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if file and assistant.doc_processor.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        result = assistant.upload_document(file_path)
        os.remove(file_path)  # Clean up
        
        return jsonify(result)
    
    return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle question asking"""
    data = request.get_json()
    question = data.get('question', '')
    
    if not question.strip():
        return jsonify({'status': 'error', 'message': 'Question cannot be empty'}), 400
    
    result = assistant.ask_question(question)
    return jsonify(result)

@app.route('/stats')
def get_stats():
    """Get system statistics"""
    stats = assistant.get_system_stats()
    return jsonify(stats)

@app.route('/clear', methods=['POST'])
def clear_memory():
    """Clear conversation memory"""
    assistant.memory.clear()
    return jsonify({'status': 'success', 'message': 'Memory cleared'})

if __name__ == '__main__':
    if config.OPENAI_API_KEY == 'your-openai-api-key-here':
        print("⚠️  Please set your OpenAI API key in the environment variable 'OPENAI_API_KEY'")
        print("   You can do this by running: export OPENAI_API_KEY='your-actual-api-key'")
        exit(1)
    
    print("🚀 Starting Healthcare AI Knowledge Assistant...")
    print("📚 Features: Document upload, Vector database, Conversational AI")
    print("🌐 Access at: http://localhost:5000")
    print("⚠️  Important: This tool is for informational purposes only.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
