---
name: agent-api-demo
description: Use when the agent needs to create, query, update, or delete the local user's demo notes through the DeerFlow FastAPI Gateway.
---

# Agent API Demo

This skill demonstrates how an agent calls a FastAPI endpoint through a small
command-line adapter. The adapter sends JSON over HTTP to the running Gateway;
the Gateway applies normal authentication, user isolation, validation, and
database persistence.

## Commands

Set `DEERFLOW_API_BASE_URL` when the Gateway is not at `http://127.0.0.1:8001`.
When authentication is enabled, set `DEERFLOW_API_TOKEN` to a PAT with the
required route access. The script prints JSON and returns a non-zero exit code
for HTTP errors.

```bash
python skills/public/agent-api-demo/scripts/call_api.py list --query "关键词"
python skills/public/agent-api-demo/scripts/call_api.py create --title "标题" --content "内容"
python skills/public/agent-api-demo/scripts/call_api.py update --id NOTE_ID --content "修改后的内容"
python skills/public/agent-api-demo/scripts/call_api.py delete --id NOTE_ID
```

Use `get --id NOTE_ID` when the complete record is needed. Only notes belonging
to the current authenticated user are returned or changed.
