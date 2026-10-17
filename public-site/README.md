# ClaimGuard frontend deployment

This folder is Vercel's project root. The project is linked to hackerjose25/IBM_Datathon and uses main as its production branch. Push frontend changes here to main to trigger a production deployment; the Python backend continues to run separately on IBM LinuxONE.

Production URL: https://claimguard-dun.vercel.app

Vercel production build settings preserve these public connection values:

- VITE_API_URL=https://claimguard-148-100-98-100.sslip.io
- VITE_WS_URL=wss://claimguard-148-100-98-100.sslip.io/ws/claims

Build: npm install, then npm run build. Output: dist/. Configuration: vercel.json. No credentials, private keys, local databases or backend source belong in this folder.

The repository also retains the local-development frontend in ../src. When changing the hosted UI, update this folder's src as well; Vercel builds public-site/src, not the root src.
