# chat.py (Final "Strict Tools" Version)
import asyncio
import os
import sys
import time
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 🔑 YOUR KEY
API_KEY = "AIzaSyBw12NQIHDAoZqmY5N69JZeP32aalgyjZI"
SERVER_SCRIPT = "server.py"

# The 2.5 list that works for you
MODEL_LIST = [
    "gemini-2.5-flash", 
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash" 
]

async def main():
    print("🔌 Connecting to Server...")
    if not os.path.exists(SERVER_SCRIPT):
        print(f"❌ Error: Cannot find {SERVER_SCRIPT}.")
        return

    # 1. Start Server
    server_params = StdioServerParameters(
        command=sys.executable, 
        args=[SERVER_SCRIPT],
        env=os.environ.copy()
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_list = await session.list_tools()
                print(f"✅ Connected! Tools: {[t.name for t in tools_list.tools]}")

                client = genai.Client(api_key=API_KEY)
                
                gemini_tools = [
                    types.Tool(function_declarations=[
                        types.FunctionDeclaration(
                            name=tool.name,
                            description=tool.description,
                            parameters=tool.inputSchema
                        ) for tool in tools_list.tools
                    ])
                ]

                # 2. FIND MODEL
                active_model = None
                chat = None
                
                # --- 🧠 SYSTEM INSTRUCTION (The Fix) ---
                # This tells the bot strictly when to use tools.
                sys_prompt = """
                You are an AI assistant with a Long-Term Memory.
                1. If the user asks you to "remember", "save", or "store" something, you MUST use the 'add_memory' tool. Do not just say you will do it.
                2. If the user asks a question about themselves or past conversations, you MUST use the 'query_memory' tool to check the database.
                """

                print("\n🔍 Connecting to Gemini 2.5...")
                for model_name in MODEL_LIST:
                    try:
                        # We inject the system instruction here
                        test_chat = client.chats.create(
                            model=model_name,
                            config=types.GenerateContentConfig(
                                tools=gemini_tools,
                                system_instruction=sys_prompt 
                            )
                        )
                        test_chat.send_message("ping")
                        active_model = model_name
                        chat = test_chat
                        break
                    except Exception as e:
                        if "429" in str(e): 
                            active_model = model_name
                            chat = client.chats.create(
                                model=model_name,
                                config=types.GenerateContentConfig(
                                    tools=gemini_tools,
                                    system_instruction=sys_prompt
                                )
                            )
                            break
                
                if not active_model:
                    print("\n❌ CRITICAL: No working models found.")
                    return

                print(f"\n🤖 Bot Ready using [{active_model}]! (Type 'exit' to quit)\n")

                # 3. CHAT LOOP
                while True:
                    user_input = input("You: ")
                    if user_input.lower() in ["exit", "quit"]:
                        break

                    # Retry Loop
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            response = chat.send_message(user_input)
                            
                            # Handle Tool Calls
                            while response.function_calls:
                                for part in response.function_calls:
                                    print(f"   (🛠️  Using tool: {part.name}...)")
                                    result = await session.call_tool(part.name, part.args)
                                    
                                    response = chat.send_message(
                                        types.Part.from_function_response(
                                            name=part.name,
                                            response={"result": result.content}
                                        )
                                    )
                            
                            print(f"Bot: {response.text}")
                            break 

                        except Exception as e:
                            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                                wait_time = 15
                                print(f"   ⏳ High Traffic. Waiting {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                print(f"❌ Error: {e}")
                                break

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())