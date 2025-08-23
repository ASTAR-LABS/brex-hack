#!/bin/bash

echo "1. Store GitHub credentials and get session token:"
SESSION_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/actions/integrations/connect \
  -H "Content-Type: application/json" \
  -d '{
    "github_token": "YOUR_GITHUB_TOKEN",
    "github_owner": "ASTAR-LABS", 
    "github_repo": "brex-hack"
  }' | jq -r '.session_token')

echo "Session token: $SESSION_TOKEN"

echo -e "\n2. Extract actions from text:"
curl -X POST http://localhost:8000/api/v1/actions/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Create a PR comment saying the code looks good and schedule a meeting tomorrow at 3pm"
  }' | jq

echo -e "\n3. Execute an action (replace ACTION_ID):"
echo "curl -X POST http://localhost:8000/api/v1/actions/execute/ACTION_ID \\"
echo "  -H \"X-Session-Token: $SESSION_TOKEN\""

echo -e "\n4. Check action status (replace ACTION_ID):"
echo "curl http://localhost:8000/api/v1/actions/status/ACTION_ID"