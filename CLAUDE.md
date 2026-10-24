# 识字蛇形棋 (Hanzi Snakes & Ladders)

A children's Chinese-character snakes-and-ladders web game. Static site on GitHub Pages:
https://jinhy1007.github.io/Hanzi-Snake-Ladder/ (repo jinhy1007/Hanzi-Snake-Ladder, branch `main`).
Players are mostly kids in the US. README.md has the full feature notes.

## How I like to work
- Reply in Chinese when I write Chinese, English when I write English.
- Always preview locally first and ask me before publishing (pushing to `main`).
- Keep everything kid-friendly.
- Generate images and voice clips one at a time so I can check them. Never trim the ends of sound clips.
- Never put API keys or secrets in chat or in the repo. They live in the Cloudflare Worker secrets and the `KIE_API_KEY` environment variable.

## Git workflow
1. At the start of every session, switch to `main` and `git pull`.
2. Merge into `main` and push only after the change passes local preview or testing (and I've said OK to publish). After pushing, delete the temporary branch, locally and on GitHub.
3. If the work isn't finished, gets stuck, or needs something only my computer has (such as the image-generation API), don't push to `main`. Leave it on a branch and tell me the branch name and what's still missing; finish and merge it next time.
4. If the live site breaks, first roll back to the last working version (`git revert`, not a force push), then look for the cause.

## Project facts
- Main code: `index.html`, `js/game.js`, `js/hints.js` (character list, built by `tools/build_hints.py`), `js/map-paths.js`, `css/style.css`, `css/fonts.css`.
- Cache version: when changing JS/CSS, bump `?v=N` in `index.html` and the matching `'vN'` in `feedbackInfo` in `js/game.js`.
- Local preview: `python3 -m http.server 8765 --bind 127.0.0.1` (also in `.claude/launch.json`).
- Publish: push to `main`, then check the Pages build with `gh api repos/jinhy1007/Hanzi-Snake-Ladder/pages/builds/latest` and confirm the live files changed.
- Cloudflare Worker `hanzi-speech-token` (source in `worker/speech-token.js`): Azure speech tokens and family sync (D1 database `hanzi-sync`). My work Mac blocks `*.workers.dev`, so test the Worker from my iPhone or home network.
- Font: subset of 文鼎 PL 中楷 (UKai), built by `tools/build_font.py`. Rebuild it when adding characters.
- Voice clips: `sounds/zi/`, made with `tools/voices.py` and `tools/voices_post.py` (Kie.ai).
- Feedback goes to a Tally form; analytics go to GoatCounter (`shizifun`). Analytics skip local previews.
