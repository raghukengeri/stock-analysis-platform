# test_imports.py
try:
    print("Testing imports...")
    
    import fastapi
    print(f"✅ FastAPI version: {fastapi.__version__}")
    
    import uvicorn
    print(f"✅ Uvicorn version: {uvicorn.__version__}")
    
    try:
        import websockets
        print(f"✅ WebSockets version: {websockets.__version__}")
    except ImportError as e:
        print(f"❌ WebSockets import failed: {e}")
    
    try:
        from fastapi import WebSocket
        print("✅ FastAPI WebSocket import successful")
    except ImportError as e:
        print(f"❌ FastAPI WebSocket import failed: {e}")
    
    try:
        from uvicorn.protocols.websockets.websockets_impl import WebSocketProtocol
        print("✅ Uvicorn WebSocket protocol import successful")
    except ImportError as e:
        print(f"❌ Uvicorn WebSocket protocol import failed: {e}")
        
    print("All core imports successful!")
    
except Exception as e:
    print(f"❌ Import test failed: {e}")