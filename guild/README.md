# Guild.ai sponsor integration (access-gated)

Guild's current docs require a Guild account. The public pricing page states there is no self-serve free trial and no published price list. Do not enter payment details for this $0 project.

At the hackathon, ask the Guild sponsor/organizer for:
1. A participant workspace or hackathon access code.
2. Confirmation that agent runtime/model credits are included at no cost.
3. The correct current SDK/CLI setup for the event workspace.

If access is granted, follow the official current quickstart:
https://docs.guild.ai/quickstart

The Guild CLI quickstart currently uses:
```bash
npm install -g @guildai/cli
guild auth login
guild auth status
```

Do not claim Guild is integrated until a FixIt-specific agent has been run and a Guild session/trace is visible. The app works without Guild; Cognee is the implemented persistent-memory sponsor integration. Local smoke tests are in `backend/evaluate.py`.
