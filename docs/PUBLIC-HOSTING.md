# Public deployment — verified 18 October 2026

Frontend: https://claimguard-dun.vercel.app
Public LinuxONE API: https://claimguard-148-100-98-100.sslip.io

The user explicitly approved public HTTPS access. Installed nginx/certbot on LinuxONE, added a narrow firewall rule for TCP 80/443, verified inbound reachability, and obtained a valid Let's Encrypt certificate with HTTP-to-HTTPS redirect. FastAPI remains on 127.0.0.1:8000. Certificate renewal is scheduled by certbot. The Vercel frontend uses HTTPS/WSS directly; its operation no longer requires the local SSH tunnel, which was stopped during verification.

## Verification

- Verified valid HTTPS, HTTP 200 health, s390x architecture, disk-loaded model, and exact CORS origin https://claimguard-dun.vercel.app.
- Started the synthetic stream using the public Vercel UI and received all 100 processed claim events over WSS.
- Recorded a labelled synthetic verification disposition, fetched it through a fresh HTTPS client, then reloaded the public browser and confirmed Saved: REVIEW.
- Confirmed public direct claim ingestion returns 403, /docs returns 404, unrelated browser origins return 403, and OPTIONS preflight returns 204.
- Evidence: evidence/public-verification.json, evidence/public-connected.png, evidence/public-certificate.log, evidence/public-nginx-deployed.conf. Public stream elapsed time includes waiting for the UI action and pacing; it is not a throughput benchmark.
- Reproduce observer: python -m scripts.verify_public --url https://claimguard-148-100-98-100.sslip.io --origin https://claimguard-dun.vercel.app, then start the stream in the UI. This writes a labelled synthetic test disposition.

## Public access scope

This is a public shared synthetic demonstration, not authenticated reviewer access. Anyone with the URL can read synthetic claims, start a bounded stream and record demo dispositions. Browser-origin restrictions are not user authentication. The proxy bounds request sizes/rates and connection counts, fixes public stream batches at 100 claims with 1-second pacing, and exposes only the necessary routes. No real patient data, credentials or insurer submissions may be added.

The prepared template is deploy/public-api.nginx.conf; the actual certificate-enabled configuration is captured in evidence/public-nginx-deployed.conf. HTTPS is configured on the VM, and Vercel's build already points to this hostname. The earlier Sites registration remains unpublished.

## Automatic startup and process recovery — enabled

Following explicit user approval, installed and enabled deploy/claimguard.service and deploy/claimguard-web-ports.service. The API now runs under systemd as linux1, bound to 127.0.0.1:8000, with IBM_LINUXONE profile and Restart=on-failure (3-second retry). The web-port unit checks/restores only the approved TCP 80/443 rule after netfilter-persistent.service and before nginx. Nginx and the certificate-renewal timer are also enabled.

Verified systemd unit syntax, active/enabled state, and the existing firewall rule. A controlled API process failure changed MainPID from 6337 to 6431 and incremented NRestarts to 1; the service returned to active/running. Public HTTPS was HEALTHY, the disk model was loaded, the saved REVIEW disposition remained available, and the public browser reconnected. Evidence: evidence/recovery-verification.json.

A full VM reboot was not performed. Startup is configured but whole-VM reboot recovery is not empirically verified. An interrupted in-memory stream batch is not resumed automatically; reload the dashboard and start a new batch if needed. Saved claims and audit records remain in the existing SQLite database.

Operational commands on the VM: sudo systemctl status claimguard.service; sudo journalctl -u claimguard.service; sudo systemctl restart claimguard.service. No local frontend or SSH tunnel is required for the public app.