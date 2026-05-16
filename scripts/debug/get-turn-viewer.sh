# All data, including system prompts

curl -s http://127.0.0.1:8765/turn_viewer/data | jq -r '.turns[] |
  "--- TURN \(.turn) ---\n",
  "--- BEGIN RULES PIPELINE     ---\n\(.prompts.rules.system)\n---\n\(.prompts.rules.user)\n--- OUTPUT ---\n\(.prompts.rules.output)\n\n--- END RULES PIPELINE ---\n\n",
  "--- BEGIN NARRATE PIPELINE ---\n\(.prompts.narrate.system)\n---\n\(.prompts.narrate.user)\n--- OUTPUT ---\n\(.prompts.narrate.output)\n\n--- END NARRATE PIPELINE ---\n\n",
  "--- BEGIN SCENE PIPELINE ---\n\(.prompts.scene.system)\n---\n\(.prompts.scene.user)\n--- OUTPUT ---\n\(.prompts.scene.output)\n\n--- END SCENE PIPELINE ---\n\n",
  "--- BEGIN STATE PIPELINE ---\n\(.prompts.state.system)\n---\n\(.prompts.state.user)\n--- OUTPUT ---\n\(.prompts.state.output)\n\n--- END STATE PIPELINE ---\n\n",
  "--- BEGIN PROGRESS PIPELINE ---\n\(.prompts.progress.system)\n---\n\(.prompts.progress.user)\n--- OUTPUT ---\n\(.prompts.progress.output)\n\n--- END PROGRESS PIPELINE ---\n\n"
'

# Only user + output, skip system prompts for easier reading

curl -s http://127.0.0.1:8765/turn_viewer/data | jq -r '.turns[] |
  "--- TURN \(.turn) ---\n",
  "--- BEGIN RULES PIPELINE     ---\n\(.prompts.rules.user)\n--- OUTPUT ---\n\(.prompts.rules.output)\n\n--- END RULES PIPELINE ---\n\n",
  "--- BEGIN NARRATE PIPELINE ---\n\(.prompts.narrate.user)\n--- OUTPUT ---\n\(.prompts.narrate.output)\n\n--- END NARRATE PIPELINE ---\n\n",
  "--- BEGIN SCENE PIPELINE ---\n\(.prompts.scene.user)\n--- OUTPUT ---\n\(.prompts.scene.output)\n\n--- END SCENE PIPELINE ---\n\n",
  "--- BEGIN STATE PIPELINE ---\n\(.prompts.state.user)\n--- OUTPUT ---\n\(.prompts.state.output)\n\n--- END STATE PIPELINE ---\n\n",
  "--- BEGIN PROGRESS PIPELINE ---\n\(.prompts.progress.user)\n--- OUTPUT ---\n\(.prompts.progress.output)\n\n--- END PROGRESS PIPELINE ---\n\n"
'
