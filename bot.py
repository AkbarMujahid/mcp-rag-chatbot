# bot.py (The Scavenger - Infinite Retry)
import os
import time
import sys
import uuid
import chromadb
import pypdf
from chromadb.config import Settings
from google import genai
from google.genai import types

# 🔑 YOUR NEW KEY
API_KEY = "AIzaSyBw12NQIHDAoZqmY5N69JZeP32aalgyjZI"

# 🧠 DATABASE SETUP
DB_PATH = "./memory_storage_unified"
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

print("🧠 Loading Memory...", end=" ")
chroma_client = chromadb.PersistentClient(
    path=DB_PATH,
    settings=Settings(anonymized_telemetry=False) 
)
collection = chroma_client.get_or_create_collection(name="user_memory")
print("✅ Done.")

# 🔌 CLIENT SETUP
client = genai.Client(api_key=API_KEY)

# 📋 THE MODEL SCAVENGER LIST
# We try these in order for EVERY message.
MODEL_ROSTER = [
    "gemini-2.0-flash-exp",   # Newest (Fast)
    "gemini-2.5-flash",       # Standard
    "gemini-1.5-flash",       # Old Reliable
    "gemini-1.5-flash-8b",    # Lightweight (Best for avoiding limits)
    "gemini-1.5-pro"          # Heavy (Slow but smart)
]

# 🛠️ TOOLS & PROMPTS
tool_definitions = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="add_memory",
            description="Save info.",
            parameters=types.Schema(
                type="OBJECT",
                properties={"text": types.Schema(type="STRING")},
                required=["text"]
            )
        ),
        types.FunctionDeclaration(
            name="query_memory",
            description="Search memory.",
            parameters=types.Schema(
                type="OBJECT",
                properties={"question": types.Schema(type="STRING")},
                required=["question"]
            )
        )
    ])
]

sys_prompt = "You are a helpful assistant with Long-Term Memory. Use query_memory to answer questions about the past."

print("\n🤖 Bot Ready! (Scavenger Mode)")
print("   (I will try 5 different models for every message to ensure success.)\n")

# 🔄 MAIN LOOP
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    if user_input.lower().startswith("/learn"):
        # (File reading logic removed for brevity - focus on chatting first)
        print("   (File reader disabled for this test to save quota.)")
        continue 

    # 🛡️ THE SCAVENGER LOOP
    success = False
    
    # We try every model in the list
    for model_name in MODEL_ROSTER:
        if success: break
        
        try:
            # print(f"   👉 Trying {model_name}...", end=" ")
            
            # Create a fresh chat for this message
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    tools=tool_definitions,
                    system_instruction=sys_prompt
                )
            )
            
            response = chat.send_message(user_input)

            # Handle Tools
            while response.function_calls:
                for part in response.function_calls:
                    fn_name = part.name
                    args = part.args
                    
                    result_text = ""
                    if fn_name == "add_memory":
                        text = args.get("text")
                        print(f"   (💾 Saving to DB...)")
                        emb_resp = client.models.embed_content(
                            model="models/text-embedding-004", contents=text
                        )
                        collection.add(
                            documents=[text],
                            embeddings=[emb_resp.embeddings[0].values],
                            ids=[str(uuid.uuid4())]
                        )
                        result_text = "Saved."
                        
                    elif fn_name == "query_memory":
                        q = args.get("question")
                        print(f"   (🔍 Searching DB...)")
                        emb_resp = client.models.embed_content(
                            model="models/text-embedding-004", contents=q
                        )
                        results = collection.query(
                            query_embeddings=[emb_resp.embeddings[0].values], 
                            n_results=3
                        )
                        found = results["documents"][0] if results["documents"][0] else []
                        result_text = "\n".join(found) if found else "No memories found."

                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result_text}
                        )
                    )

            print(f"Bot: {response.text}")
            success = True # We got an answer!
            
        except Exception as e:
            # print(f"❌ Failed ({e})")
            continue # Try the next model immediately

    if not success:
        print("\n❌ All models are busy. You are temporarily Rate Limited.")
        print("   Please wait 60 seconds and try again.")