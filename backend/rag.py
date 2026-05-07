from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.prebuilt import create_react_agent
from pypdf import PdfReader

_BASE_DIR = Path(__file__).parent

_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
_vectorstore = Chroma(
    collection_name="pdf_docs",
    embedding_function=_embeddings,
    persist_directory=str(_BASE_DIR / "chroma_db"),
)
_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


@tool
def retrieve_documents(query: str) -> str:
    """Search the knowledge base and return the text of the most relevant document chunks."""
    docs = _vectorstore.similarity_search(query, k=4)
    return "\n\n".join(doc.page_content for doc in docs)


_llm = ChatOpenAI(model="gpt-4o")
_agent = create_react_agent(_llm, [retrieve_documents])


def ingest(file_path: str) -> None:
    reader = PdfReader(file_path)
    texts = [t for page in reader.pages if (t := page.extract_text())]
    text = "\n".join(texts)
    chunks = _splitter.split_documents([Document(page_content=text, metadata={"source": file_path})])
    _vectorstore.add_documents(chunks)


def query(question: str) -> str:
    result = _agent.invoke({"messages": [{"role": "user", "content": question}]})
    content = result["messages"][-1].content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if b.get("type") == "text")
    return content or "No answer found."
