import logging
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from pydantic import BaseModel
from pypdf import PdfReader

import config

_BASE_DIR = Path(__file__).parent

_embeddings = OpenAIEmbeddings(model=config.EMBED_MODEL)
_vectorstore = Chroma(
    collection_name=config.VECTORSTORE_COLLECTION_NAME,
    embedding_function=_embeddings,
    persist_directory=str(_BASE_DIR / config.VECTORSTORE_PERSIST_DIR),
)
_splitter = RecursiveCharacterTextSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)


@tool
def retrieve_documents(query: str) -> str:
    """Search the knowledge base and return the text of the most relevant document chunks."""
    logger.debug("retrieve: %r", query)
    docs = _vectorstore.similarity_search(query, k=config.TOP_K)
    logger.debug("retrieved %d docs", len(docs))
    return "\n\n".join(doc.page_content for doc in docs)


class _Score(BaseModel):
    score: float


_llm = ChatOpenAI(model=config.LLM_MODEL)
_scorer = _llm.with_structured_output(_Score)
_tools = [retrieve_documents]
_tools_by_name = {t.name: t for t in _tools}
_llm_with_tools = _llm.bind_tools(_tools)


@task
def _call_llm(messages):
    return _llm_with_tools.invoke(messages)


@task
def _call_tool(tool_call):
    return _tools_by_name[tool_call["name"]].invoke(tool_call)


@entrypoint()
def _agent(messages):
    response = _call_llm(messages).result()
    while True:
        if not response.tool_calls:
            break
        tool_results = [_call_tool(tc).result() for tc in response.tool_calls]
        messages = add_messages(messages, [response, *tool_results])
        response = _call_llm(messages).result()
    return add_messages(messages, response)


def ingest(file_path: str) -> None:
    logger.debug("reading pdf: %s", file_path)
    reader = PdfReader(file_path)
    texts = [t for page in reader.pages if (t := page.extract_text())]
    text = "\n".join(texts)
    logger.debug("pdf pages: %d, chars: %d", len(reader.pages), len(text))
    chunks = _splitter.split_documents([Document(page_content=text, metadata={"source": file_path})])
    logger.debug("chunks: %d", len(chunks))
    _vectorstore.add_documents(chunks)
    logger.info("vectorstore updated: %d chunks from %s", len(chunks), file_path)


def query(question: str) -> str:
    logger.debug("running agent")
    result = _agent.invoke([HumanMessage(content=question)])
    content = result[-1].content
    if isinstance(content, list):
        content = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
    content = content or "No answer found."

    scored: _Score = _scorer.invoke([
        HumanMessage(content=(
            f"Question: {question}\n\nAnswer: {content}\n\n"
            "Rate how well this answer is supported by the retrieved knowledge. "
            "Return a score between 0.0 (no support) and 1.0 (fully supported)."
        ))
    ])
    logger.debug("confidence score: %.2f", scored.score)
    if scored.score <= config.CONFIDENCE_THRESHOLD:
        logger.warning("low confidence (%.2f), returning fallback", scored.score)
        return f"Answer confidence too low ({scored.score:.2f}). Try rephrasing your question or upload a more relevant document."
    logger.debug("query done")
    return content
