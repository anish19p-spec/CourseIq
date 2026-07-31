import os 
import json 
from pathlib import Path
from typing import Any, cast
import chromadb
from dotenv import load_dotenv
from google import genai

load_dotenv()

chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="documents",
    metadata={"Description": "documentation for RAG agent"},
)


def _get_genai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required for embeddings.")
    return genai.Client(api_key=api_key)


def _embed_text(text: str) -> list[float]:
    client = _get_genai_client()
    response = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )

    if not response.embeddings:
        raise ValueError("Gemini did not return any embeddings.")

    embedding = response.embeddings[0]
    if not embedding.values:
        raise ValueError("Gemini returned an empty embedding vector.")

    return list(embedding.values)

def main():
    vector = _embed_text("Dr. Smith is a great professor")

    if vector:
        print(f"Success! Vector length: {len(vector)}")
        print("Vector Database and AI Client are ready.")
    else:
        print("Error: No embeddings returned from the API.")
    
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.

    Why overlap? So we don't cut important context in half.
    A question might span two chunks - overlap helps with that.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at a sentence boundary
        if end < len(text):
            # Look for last period, question mark, or newline
            last_break = max(chunk.rfind(". "), chunk.rfind("? "), chunk.rfind("\n"))
            if last_break > chunk_size // 2:  # Only if we're past halfway
                end = start + last_break + 1
                chunk = text[start:end]

        chunks.append(chunk.strip())
        start = end - overlap  # Overlap with previous chunk

    return [c for c in chunks if c]  # Remove empty chunks


def load_and_index_documents(docs_path: str):
    """
    Load all documents from a directory and index them.
    """
    docs_dir = Path(docs_path)

    if not docs_dir.exists():
        print(f"Creating docs directory: {docs_path}")
        docs_dir.mkdir(parents=True)
        return
    
    

    indexed_count = 0

    for file_path in docs_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in [
            ".txt",
            ".md",
            ".py",
            ".js",
            ".ts",
        ]:
            try:
                content = file_path.read_text(encoding="utf-8")

                # Skip very small files
                if len(content) < 50:
                    continue

                # Chunk the document
                chunks = chunk_text(content)

                # Create embeddings for all chunks at once (faster)
                embeddings = [_embed_text(chunk) for chunk in chunks]

                # Prepare data for ChromaDB
                ids = [f"{file_path.name}_{i}" for i in range(len(chunks))]
                metadatas = [
                    {"source": str(file_path), "chunk_index": i}
                    for i in range(len(chunks))
                ]

                # Add to collection
                collection.add(
                    ids=cast(Any, ids),
                    embeddings=cast(Any, embeddings),
                    documents=cast(Any, chunks),
                    metadatas=cast(Any, metadatas),
                )

                indexed_count += len(chunks)
                print(f"Indexed: {file_path.name} ({len(chunks)} chunks)")

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    print(f"\nTotal chunks indexed: {indexed_count}")


def search_documents(query: str, n_results: int = 5) -> list[dict]:
    """
    Search the vector store for relevant documents.

    Returns a list of results with content and metadata.
    """
    # Embed the query
    query_embedding = _embed_text(query)

    # Search ChromaDB
    results: Any = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    # Format results
    formatted = []
    for i in range(len(results["documents"][0])):
        formatted.append(
            {
                "content": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "relevance_score": 1
                - results["distances"][0][i],  # Convert distance to similarity
            }
        )

    return formatted

TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": """Search the indexed documents for relevant information.

Use this tool when you need to find information to answer a question.
The search uses semantic similarity - phrase your query naturally.

IMPORTANT:
- Search BEFORE answering questions about the documents
- You can search multiple times with different queries
- If results aren't relevant, try rephrasing your search""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific and natural.",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 10)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "list_available_documents",
        "description": "List all documents that have been indexed. Use this to understand what knowledge is available.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

# ============================================================
# Implementation of tool functions
# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================


def search_knowledge_base(query: str, num_results: int = 5) -> str:
    """Execute a search and format results for the agent."""
    num_results = min(num_results, 10)  # Cap at 10

    results = search_documents(query, n_results=num_results)

    if not results:
        return "No relevant documents found. Try a different search query."

    formatted = f"Found {len(results)} relevant document sections:\n\n"

    for i, r in enumerate(results, 1):
        formatted += f"--- Result {i} (relevance: {r['relevance_score']:.2f}) ---\n"
        formatted += f"Source: {r['source']}\n"
        formatted += f"Content:\n{r['content']}\n\n"

    return formatted


def list_available_documents() -> str:
    """List all indexed documents."""
    # Get all unique sources from the collection
    all_data = collection.get(include=["metadatas"])

    if not all_data["metadatas"]:
        return "No documents have been indexed yet."

    sources = set()
    for metadata in all_data["metadatas"]:
        sources.add(metadata["source"])

    result = f"Indexed documents ({len(sources)} files):\n\n"
    for source in sorted(sources):
        result += f"  - {source}\n"

    return result


# Map tool names to implementations
def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool and return the result."""
    try:
        if name == "search_knowledge_base":
            return search_knowledge_base(
                arguments.get("query", ""), arguments.get("num_results", 5)
            )
        elif name == "list_available_documents":
            return list_available_documents()
        else:
            return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error executing {name}: {str(e)}"


# ============================================================
# THE RAG AGENT
#  ==========================================================
def run_rag_agent(question: str, max_iterations: int = 10) -> str:
    """
    Run the RAG agent to answer a question.

    The agent will:
    1. Search the knowledge base for relevant context
    2. Ask Gemini to synthesize an answer from the retrieved information
    3. Cite its sources
    """

    print("\n" + "=" * 60)
    print("RAG AGENT")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")
    print("-" * 60)

    # Retrieve context first, then ask Gemini to synthesize an answer.
    search_results = search_knowledge_base(question)

    if search_results.startswith("No relevant documents found"):
        return search_results

    system_prompt = """You are a knowledgeable assistant with access to a document knowledge base.

## Your Approach

When answering questions:

1. **SEARCH FIRST** - Always search the knowledge base before answering questions about the documents
2. **BE THOROUGH** - If your first search doesn't give good results, try different search terms
3. **CITE SOURCES** - Reference which documents your information comes from
4. **BE HONEST** - If the information isn't in the documents, say so

## Guidelines

- Use natural language for search queries
- Combine information from multiple sources when relevant
- If asked about something not in the documents, clearly state that

## Response Format

When you have enough information, structure your answer as:

**Answer:** [Your comprehensive answer]

**Sources:**
- [List the source documents you used]

If you cannot find relevant information, explain what you searched for and suggest the user might need to provide more documents."""

    prompt = (
        f"{system_prompt}\n\n"
        f"Question:\n{question}\n\n"
        f"Retrieved context:\n{search_results}\n\n"
        "Write a concise answer using only the retrieved context. Include sources."
    )

    client = _get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    final_answer = getattr(response, "text", None) or "No answer returned from Gemini."

    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(f"\n{final_answer}\n")

    return final_answer

    return "Max iterations reached. The agent could not complete the task."





if __name__ == "__main__":
    load_and_index_documents("./docs")
    search_results = search_documents("What does Dr. Smith say about machine learning?")
    print("\nSearch Results:")
    for res in search_results:
        print(f"- {res['source']} (score: {res['relevance_score']:.4f})")
        print(f"  {res['content'][:200]}...")
    
    
    
 