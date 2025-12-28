🧠 Resilient RAG AI Agent (MCP Architecture)
A locally-hosted AI assistant that reads files, remembers facts, and survives API outages.

🚀 Overview
Standard LLMs suffer from "Context Windows" and "Amnesia"—once you close the chat, they forget everything.

This project is a Retrieval-Augmented Generation (RAG) system built to solve that. It runs locally on your machine, using ChromaDB to store vector embeddings of your conversations and documents. It is architected around Model Context Protocol (MCP) concepts, giving the AI "tools" to autonomously decide when to save a memory, search its database, or read a file.

Built by: Akbar Mujahid | B.E. Final Year Student

⚙️ How It Works (The Architecture)
This agent uses a Tool-Use Loop to interact with the world:

Ingestion: You feed it a file (/learn notes.pdf). The bot chunks the text and converts it into vector embeddings.

Storage: These embeddings are stored locally in memory_storage_unified (ChromaDB).

Retrieval: When you ask a question, the AI doesn't just guess. It generates a search query, retrieves the most relevant "chunks" from the database, and uses them to answer.

Resilience: If the primary model (Gemini 2.5) is busy, the "Scavenger" logic automatically reroutes the request to Gemini 2.0 or Gemini 1.5-8b to ensure 99.9% uptime.

⚡ Key Features
🧠 Long-Term Memory: Remembers your name, project details, and preferences across restarts.

👀 Document Vision: Drag-and-drop file reading. Supports .pdf, .txt, .md, and .py.

🛡️ "Scavenger" Resilience: Features an exponential backoff system that tries 4 different Google models if one hits a Rate Limit.

🔧 Autonomous Tool Use: The AI decides when to use memory. It isn't hard-coded; the LLM uses logic to pick the right tool (MCP Pattern).

🛠️ Tech Stack
Language: Python 3.10+

LLM Provider: Google GenAI SDK (Gemini 2.5 Flash, 2.0 Flash, 1.5 Flash-8b)

Vector Database: ChromaDB (Local, Persistent)

File Parsing: PyPDF (for PDF ingestion)

📥 Installation & Setup
1. Clone the Repository
Bash

git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
2. Install Dependencies
Bash

pip install google-genai chromadb pypdf
3. Configure API Key
Open bot.py and replace the placeholder with your Google Gemini API Key. (Note: In a production environment, use environment variables. For this demo, direct insertion is used for simplicity.)

Python

# bot.py
API_KEY = "YOUR_ACTUAL_API_KEY_HERE"
🚀 Usage Guide
Start the Bot
Run the unified script:

Bash

python bot.py
Commands
Chat: Just type naturally! "Hi, my name is Akbar."

Read a File: Use the /learn command with a file path.

Plaintext

/learn C:\Users\Akbar\Documents\Exam_Notes.pdf
Exit: Type exit or quit.

Example Workflow
Plaintext

You: /learn my_project_details.txt
Bot: 📖 Opening... 📄 Text Read... 💾 Memorizing... ✅ Done!

You: What tech stack does my project use?
Bot: (🔍 Searching DB...) Your project uses Flutter and Firebase.
📂 Project Structure
bot.py: The core logic. Contains the Chat Loop, Tool Definitions, and Retry Logic.

memory_storage_unified/: The folder automatically created by ChromaDB. Do not delete this unless you want to wipe the bot's memory.

🔮 Future Improvements
[ ] Add Web Search capabilities using Google Search API.

[ ] Build a Streamlit UI for a web-based interface.

[ ] Add support for image analysis.

📜 License
This project is open-source and available under the MIT License.
