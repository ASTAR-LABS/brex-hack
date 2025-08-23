#!/usr/bin/env python3
"""
Test the complete action flow:
1. Connect integration (store GitHub credentials)
2. Extract actions from text
3. Execute an action
4. Check action status
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_flow():
    async with httpx.AsyncClient() as client:
        print("1. Connecting GitHub integration...")
        connect_response = await client.post(
            f"{BASE_URL}/actions/integrations/connect",
            json={
                "github_token": "your_github_token_here",
                "github_owner": "ASTAR-LABS",
                "github_repo": "brex-hack"
            }
        )
        session_token = connect_response.json()["session_token"]
        print(f"   Session token: {session_token}")
        
        print("\n2. Extracting actions from text...")
        extract_response = await client.post(
            f"{BASE_URL}/actions/extract",
            json={
                "text": "Create a PR comment saying the feature is ready for review and schedule a meeting tomorrow at 3pm to discuss the implementation"
            }
        )
        actions = extract_response.json()["actions"]
        print(f"   Found {len(actions)} actions:")
        for action in actions:
            print(f"   - {action['type']}: {action['description']} (confidence: {action['confidence']})")
        
        if actions:
            print("\n3. Executing first action...")
            first_action = actions[0]
            
            from app.services.action_executor_service import ActionExecutorService
            executor = ActionExecutorService()
            stored_action = await executor.add_action(
                action_type=first_action["type"],
                description=first_action["description"],
                confidence=first_action["confidence"],
                metadata={"pr_number": 7}
            )
            
            exec_response = await client.post(
                f"{BASE_URL}/actions/execute/{stored_action.id}",
                headers={"X-Session-Token": session_token}
            )
            print(f"   Execution result: {exec_response.json()}")
            
            print("\n4. Checking action status...")
            status_response = await client.get(
                f"{BASE_URL}/actions/status/{stored_action.id}"
            )
            status = status_response.json()
            print(f"   Status: {status['state']}")
            if status.get('error'):
                print(f"   Error: {status['error']}")
            if status.get('result'):
                print(f"   Result: {json.dumps(status['result'], indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_flow())