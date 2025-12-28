# server.py (Diagnostic Version)
import sys
import os

# 1. 🛑 ERROR TRAP: Catch crash errors instantly
try:
    import asyncio
    import uuid
    import chromadb
    from chromadb.config import Settings
    from google import genai
    from mcp.server.models import InitializationOptions
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server
    from pydantic import BaseModel

    # 🔑 YOUR KEY
    API_KEY = "AIzaSyBw12NQIHDAoZqmY5N69JZeP32aalgyjZI"

    # --- Safety Patch ---
    try:
        from mcp.types import NotificationOptions
    except ImportError:
        class NotificationOptions(BaseModel):
            tools_changed: bool = False
            resources_changed: bool = False
            prompts_changed: bool = False

    # 2. 📂 NEW STORAGE PATH (Bypasses old locks)
    NEW_DB_PATH = "./my_memory_new"
    
    # Initialize Database
    chroma_client = chromadb.PersistentClient(
        path=NEW_DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    collection = chroma_client.get_or_create_collection(name="bot_memory")
    
    client = genai.Client(api_key=API_KEY)
    app = Server("MemoryServer")

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="add_memory",
                description="Save important information.",
                inputSchema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"]
                }
            ),
            Tool(
                name="query_memory",
                description="Search memory.",
                inputSchema={
                    "type": "object",
                    "properties": {"question": {"type": "string"}},
                    "required": ["question"]
                }
            )
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "add_memory":
            text = arguments.get("text")
            print(f"   [LOG] Saving: {text[:30]}...", file=sys.stderr)
            
            response = client.models.embed_content(
                model="models/text-embedding-004", contents=text
            )
            collection.add(
                documents=[text],
                embeddings=[response.embeddings[0].values],
                ids=[str(uuid.uuid4())]
            )
            return [TextContent(type="text", text="Saved.")]

        if name == "query_memory":
            question = arguments.get("question")
            print(f"   [LOG] Searching: {question[:30]}...", file=sys.stderr)
            
            response = client.models.embed_content(
                model="models/text-embedding-004", contents=question
            )
            results = collection.query(
                query_embeddings=[response.embeddings[0].values], n_results=3
            )
            found = results["documents"][0] if results["documents"][0] else []
            return [TextContent(type="text", text="\n".join(found) if found else "Nothing found.")]
        
        raise ValueError(f"Unknown tool: {name}")

    async def main():
        async with stdio_server() as (read, write):
            options = NotificationOptions() 
            await app.run(
                read, write,
                InitializationOptions(
                    server_name="memory",
                    server_version="0.1.0",
                    capabilities=app.get_capabilities(notification_options=options),
                ),
            )

    if __name__ == "__main__":
        asyncio.run(main())

except Exception as e:
    # 🚨 CRASH RECORDER: Writes the error to a file so we can see it
    with open("crash_report.txt", "w") as f:
        f.write(f"CRASH REPORT:\n{str(e)}")
    sys.exit(1)