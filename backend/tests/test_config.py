import config


def test_embed_model():
    assert config.EMBED_MODEL == "text-embedding-3-small"


def test_vectorstore_collection_name():
    assert config.VECTORSTORE_COLLECTION_NAME == "pdf_docs"


def test_vectorstore_persist_dir():
    assert config.VECTORSTORE_PERSIST_DIR == "chroma_db"


def test_chunk_size():
    assert config.CHUNK_SIZE == 1000


def test_chunk_overlap():
    assert config.CHUNK_OVERLAP == 200


def test_top_k():
    assert config.TOP_K == 4


def test_llm_model():
    assert config.LLM_MODEL == "gpt-4o"


def test_confidence_threshold():
    assert config.CONFIDENCE_THRESHOLD == 0.8


def test_file_size_limit():
    assert config.FILE_SIZE_LIMIT == 5 * 1024 * 1024


def test_accepted_file_types():
    assert config.ACCEPTED_FILE_TYPES == ".pdf"
