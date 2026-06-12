# Security

Do not commit `Z:\job\02_tarot_bot\.env`.

Keep `BOT_TOKEN` only in the backend bot environment. Never store it in
`astra-tarot-miniapp-react`, GitHub Pages, browser code, screenshots, chats, or
logs.

Keep `GEMINI_API_KEY` only in the backend bot environment. The frontend must
call backend APIs and must never know the Gemini key.

If a token or API key was posted to an archive, chat, issue, pull request,
commit history, or public repository, revoke and reissue it immediately.
