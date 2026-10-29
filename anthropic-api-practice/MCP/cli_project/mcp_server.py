from pydantic import Field

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# TODO: Write a tool to read a doc
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string."
)
def read_document(
    doc_id: str = Field(description="Id of the document to read")
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    
    return docs[doc_id]

# Tool to edit a doc
@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string."
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(description="The text to replace. Must match exactly, including whitespace."),
    new_str: str = Field(description="The new text to insert in place of the old text.")
) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    
    docs[doc_id] = docs[doc_id].replace(old_str, new_str)
    return f"Successfully updated document '{doc_id}'."


# Resource: Return all doc IDs
@mcp.resource(
    uri="docs://documents",
    name="list_documents",
    description="List all available document IDs in the repository."
)
def list_document_ids() -> list[str]:
    """Return all document keys/IDs as a list."""
    return list(docs.keys())


# Resource: Return the contents of a particular doc
@mcp.resource(
    uri="docs://documents/{doc_id}",
    name="get_document_content",
    description="Retrieve the text contents of a document by its ID."
)
def get_document_by_id(doc_id: str) -> str:
    """Return the raw text of a document given its doc_id."""
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]


# Prompt: Rewrite a doc in markdown format
@mcp.prompt(
    name="rewrite_markdown",
    description="Rewrite a document into clean, structured Markdown format."
)
def rewrite_doc_markdown(
    doc_id: str = Field(description="Id of the document to rewrite in markdown")
) -> str:
    """Generate a prompt asking Claude to convert the document into Markdown."""
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return (
        f"Please rewrite and format the following document ({doc_id}) into clean, "
        f"well-structured Markdown with appropriate headings and bullets:\n\n{docs[doc_id]}"
    )


# Prompt: Summarize a doc
@mcp.prompt(
    name="summarize",
    description="Generate a concise summary of a specific document."
)
def summarize_doc(
    doc_id: str = Field(description="Id of the document to summarize")
) -> str:
    """Generate a prompt asking Claude to summarize the document."""
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return (
        f"Please provide a concise, high-level summary of the following document ({doc_id}):\n\n"
        f"{docs[doc_id]}"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
