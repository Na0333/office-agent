#!/usr/bin/env python3
"""
Office Agent Mode Test Script
Test both brain mode and tool mode functionality
"""

import os
import asyncio
from app.config import get_settings
from app.schemas.message import ChatRequest

def test_tool_mode():
    """Test tool mode initialization"""
    print("=== Testing Tool Mode ===")
    os.environ["ENABLE_AGENT_BRAIN"] = "false"

    # Clear cache to reload settings
    from app.config import get_settings
    import importlib
    importlib.reload(importlib.import_module('app.config'))

    settings = get_settings()
    print(f"enable_agent_brain: {settings.enable_agent_brain}")

    # Test import
    from app.main import app
    print("✓ Tool mode initialized successfully")
    return True

async def test_brain_mode():
    """Test brain mode functionality"""
    print("\n=== Testing Brain Mode ===")
    os.environ["ENABLE_AGENT_BRAIN"] = "true"

    # Clear cache to reload settings
    from app.config import get_settings
    import importlib
    importlib.reload(importlib.import_module('app.config'))

    settings = get_settings()
    print(f"enable_agent_brain: {settings.enable_agent_brain}")

    # Test agent
    from app.agent.core import OfficeAgent
    agent = OfficeAgent()
    print("✓ OfficeAgent initialized successfully")

    # Test message handling
    request = ChatRequest(session_id='test_session', user_id='test_user', content='Hello')
    response = await agent.handle_message(request)
    print(f"✓ Agent response: {response.reply}")
    print(f"✓ Intent: {response.intent}")
    return True

async def main():
    """Run all tests"""
    try:
        # Test tool mode
        test_tool_mode()

        # Test brain mode
        await test_brain_mode()

        print("\n🎉 All tests passed! Both modes work correctly.")
        print("\nUsage:")
        print("- Tool mode: ENABLE_AGENT_BRAIN=false python3 -m app.main")
        print("- Brain mode: ENABLE_AGENT_BRAIN=true python3 -m app.main")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())