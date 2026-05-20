**AGENTS.md**

- **Dependencies** – before any code runs install the runtime packages used in the source:
  ```bash
  python -m pip install requests python-dotenv pillow
  ```

- **Environment** – the bot reads `AUC_PASSWORD` from a `.env` file in the repository root.  
  Create a file named `.env` containing:
  ```dotenv
  AUC_PASSWORD=<your‑password>
  ```

- **Database files** – `main.py` expects `db/grid.json` and `db/userdata.json`.  
  If they are missing the script will create them automatically on first start.

- **Running the bot** – from the repository root start the process with:
  ```bash
  python main.py
  ```
  *The working directory must be the repo root because the code uses relative paths (`db/...`).*

- **Network endpoint** – the bot contacts a fixed server at `http://104.236.25.60:6767/api`.  
  No configuration file changes this address; it is hard‑coded in `main.py`.

- **Core commands (sent to the bot)** – the bot only reacts to messages prefixed with `a/p`.  
  Quick reference (output of `a/p help`):
  - `a/p uptime` – reports bot start time
  - `a/p ping` – simple health check
  - `a/p status` – shows grid size, user count, total pixels placed
  - `a/p mypixels` – shows your remaining pixels / max charges
  - `a/p place <x> <y> <hex‑color>` – place a single pixel (requires at least 1 pixel left)
  - `a/p bulkplace <x> <y> <w> <h> <hex‑color>` – place a rectangle (must fit within remaining pixels, max 256×256)
  - `a/p grid` – generates `grid.png` from the JSON grid and uploads it via `tmpfiles.org`; the resulting URL is posted back
  - `a/p droplets` – shows your droplet balance
  - `a/p shop` – shows purchase options
  - `a/p buy <amount> <pixels|maxcharges|speed>` – spend droplets to gain pixels, increase max charges, or boost speed

- **CLI‑only admin commands** – typed into the running process’s console:
  - `sendacmsg <text>` – send a raw message to the chat server
  - `givepixels <user> <amt>` – add pixels to a user (capped at that user’s max charges)
  - `givemaxcharges <user> <amt>` – increase a user’s max charge limit
  - `givedroplets <user> <amt>` – add droplets to a user

- **Background workers** – two daemon threads start automatically:
  1. **`givepixels`** – every 5 seconds each user gains `speed` pixels (default 1) up to their `maxcharges`; every tick also adds 5 droplets to every user. Once a minute each user’s `maxcharges` is increased by their `speed`.
  2. **CLI input loop** – processes the admin commands above.

- **Shutdown** – pressing `Ctrl‑C` (or sending a KeyboardInterrupt) cleanly stops the socket and exits.

- **Gotchas agents often miss**
  - The **`.env` file is required**; without `AUC_PASSWORD` the login fails.
  - The bot **must be launched from the repository root** because it uses relative `db/…` paths.
  - **Database files are auto‑created** on first run; deleting them forces a fresh empty grid and user data.
  - The **hard‑coded server IP** cannot be overridden via config – agents should not assume a different endpoint.
  - **`tmpfiles.org` upload** in `a/p grid` requires internet access; failures are silently ignored in the upload helper.
