# Quick MCP Setup Guide

## 1. GitHub MCP Setup

### Get GitHub Personal Access Token:
1. Go to https://github.com/settings/tokens/new
2. Name: "Ultrathink MCP"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Optional: for GitHub Actions)
4. Click "Generate token"
5. Copy the token (starts with `ghp_`)

### Add to .env:
```bash
GITHUB_TOKEN=ghp_your_token_here
GITHUB_OWNER=your_username
GITHUB_REPO=your_repo_name
```

## 2. Google Calendar MCP Setup

### Create Google Cloud Project:
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search "Google Calendar API"
   - Click Enable

### Create OAuth 2.0 Credentials:
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure consent screen if needed:
   - User type: External
   - App name: Ultrathink
   - Add your email
   - Add scope: `../auth/calendar`
4. Application type: Web application
5. Name: "Ultrathink MCP"
6. Authorized redirect URIs: `http://localhost:8000/auth/callback`
7. Click Create
8. Copy Client ID and Client Secret

### Add to .env:
```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

## 3. Slack MCP Setup

### Create Slack App:
1. Go to https://api.slack.com/apps
2. Click "Create New App" > "From scratch"
3. App Name: "Ultrathink"
4. Pick your workspace

### Configure OAuth & Permissions:
1. Go to "OAuth & Permissions" in sidebar
2. Under "Scopes" > "Bot Token Scopes", add:
   - `chat:write` - Send messages
   - `channels:read` - View channels
   - `channels:history` - Read channel history
   - `files:write` - Upload files
   - `users:read` - View users
3. Click "Install to Workspace"
4. Authorize the app
5. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### Optional: Enable Socket Mode (for real-time):
1. Go to "Socket Mode" in sidebar
2. Enable Socket Mode
3. Generate an app-level token
4. Copy the token (starts with `xapp-`)

### Add to .env:
```bash
SLACK_BOT_TOKEN=xoxb-your_bot_token
SLACK_APP_TOKEN=xapp-your_app_token  # Optional
SLACK_DEFAULT_CHANNEL=general
```

## 4. Test Your Setup

### Restart Backend:
```bash
cd backend
python run.py
```

### Check Status:
```bash
curl http://localhost:8000/api/v1/mcp/status
```

You should see:
- GitHub: enabled and configured ✅
- Google Calendar: enabled and configured ✅
- Slack: enabled and configured ✅

### Test in Frontend:
1. Open http://localhost:3000
2. Click Settings icon (top right)
3. Each MCP should show "Ready" in green
4. Click "Test" to verify connection

## 5. Usage Examples

Once configured, you can say things like:

**GitHub:**
- "Create a GitHub issue about the login bug"
- "Comment on PR #42 saying the changes look good"
- "What PRs are open in my repo?"

**Google Calendar:**
- "Schedule a meeting tomorrow at 3pm"
- "What's on my calendar this week?"
- "Create a recurring standup every day at 10am"

**Slack:**
- "Send a message to #general saying the deployment is complete"
- "Post the error log to the dev channel"
- "What messages are in #announcements?"

## Troubleshooting

### MCP Shows "Missing Config":
- Check that all required environment variables are set
- Make sure there are no typos in the .env file
- Restart the backend after changes

### Test Connection Fails:
- Verify API keys/tokens are correct
- Check that APIs are enabled (for Google)
- Ensure app is installed to workspace (for Slack)
- Check network/firewall settings

### No Tools Available:
- Install MCP packages: `npm install -g @modelcontextprotocol/server-github @modelcontextprotocol/server-slack`
- Or let the system use npx (slower but no install needed)

## Security Notes

- Never commit .env file to git
- Rotate tokens regularly
- Use minimal required scopes
- Consider using environment-specific tokens for production