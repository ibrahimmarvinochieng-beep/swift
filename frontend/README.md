# Swift Frontend — Stay Ahead.

Sample frontend for the Swift Event Intelligence Platform. Deploy to Vercel to preview the design.

## Pages

- **/** — Landing page (Sky Gradient hero, "Swift Stay Ahead.")
- **/events** — Event feed with sample data, filters, notification
- **/events/[id]** — Event detail
- **/ingest** — Signal ingestion form
- **/login** — Login / sign up

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Deploy to Vercel

### Option 1: Vercel CLI

```bash
npm i -g vercel
cd frontend
vercel
```

### Option 2: GitHub + Vercel

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project
3. Import the repo
4. Set **Root Directory** to `frontend`
5. Deploy

### Option 3: Deploy frontend only

If `frontend` is the root of a separate repo:

1. Connect the repo to Vercel
2. Vercel auto-detects Next.js
3. Deploy

## Branding

- **Colors:** Electric Blue (#007AFF), Vibrant Orange (#FF9500), Dark Slate (#0A1628)
- **Font:** Montserrat
- **Tagline:** Stay Ahead.
