# All data, including system prompts

curl -s http://127.0.0.1:8765/turn_viewer/data | jq -r '.turns[] | select(.turn == 10) |
  "--- BEGIN RULES PIPELINE     ---\n\(.rules_prompt.system)\n---\n\(.rules_prompt.user)\n--- OUTPUT ---\n\(.rules_prompt.output)\n\n--- END RULES PIPELINE ---\n\n",
  "--- BEGIN NARRATE PIPELINE ---\n\(.narrate_prompt.system)\n---\n\(.narrate_prompt.user)\n--- OUTPUT ---\n\(.narrate_prompt.output)\n\n--- END NARRATE PIPELINE ---\n\n",
  "--- BEGIN SCENE PIPELINE ---\n\(.scene_prompt.system)\n---\n\(.scene_prompt.user)\n--- OUTPUT ---\n\(.scene_prompt.output)\n\n--- END SCENE PIPELINE ---\n\n",
  "--- BEGIN STATE PIPELINE ---\n\(.state_prompt.system)\n---\n\(.state_prompt.user)\n--- OUTPUT ---\n\(.state_prompt.output)\n\n--- END STATE PIPELINE ---\n\n",
  "--- BEGIN PROGRESS PIPELINE ---\n\(.progress_prompt.system)\n---\n\(.progress_prompt.user)\n--- OUTPUT ---\n\(.progress_prompt.output)\n\n--- END PROGRESS PIPELINE ---\n\n"
'

# Only user + output, skip system prompts for easier reading

curl -s http://127.0.0.1:8765/turn_viewer/data | jq -r '.turns[] | select(.turn == 10) |
  "--- BEGIN RULES PIPELINE     ---\n\(.rules_prompt.user)\n--- OUTPUT ---\n\(.rules_prompt.output)\n\n--- END RULES PIPELINE ---\n\n",
  "--- BEGIN NARRATE PIPELINE ---\n\(.narrate_prompt.user)\n--- OUTPUT ---\n\(.narrate_prompt.output)\n\n--- END NARRATE PIPELINE ---\n\n",
  "--- BEGIN SCENE PIPELINE ---\n\(.scene_prompt.user)\n--- OUTPUT ---\n\(.scene_prompt.output)\n\n--- END SCENE PIPELINE ---\n\n",
  "--- BEGIN STATE PIPELINE ---\n\(.state_prompt.user)\n--- OUTPUT ---\n\(.state_prompt.output)\n\n--- END STATE PIPELINE ---\n\n",
  "--- BEGIN PROGRESS PIPELINE ---\n\(.progress_prompt.user)\n--- OUTPUT ---\n\(.progress_prompt.output)\n\n--- END PROGRESS PIPELINE ---\n\n"
'
