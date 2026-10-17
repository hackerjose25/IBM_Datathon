# LinuxONE deployment — verified 18 October 2026

SSH access, Ubuntu 24.04 on s390x, Python 3.12.3, target-native model training, 34 passing backend tests, live scoring, a 100-event stream and persisted verification review have now been verified. Evidence is in ../evidence/linuxone/. The API runs in /home/linux1/claimguard and binds to 127.0.0.1:8000. The local dashboard currently reaches it through an SSH tunnel.

## Obtain access

1. Open IBM's [Datathon page](https://community.ibm.com/zsystems/datathon/) and its [LinuxONE getting-started page](https://community.ibm.com/zsystems/l1cc/).
2. Choose **Try Linux Virtual Machines on the LinuxONE Community Cloud** and register using event code **SSF2026**. Complete account activation yourself; retain credentials privately.
3. Follow the event instructions to provision the assigned VM. IBM's FAQ says the event code is needed to see AI_LAB. If activation or the lab is missing, contact the event SME team or the support contact listed on that official page. Check its current instructions before registering.
4. Obtain a working SSH alias, host, username, and your local private-key path. Never commit the key or paste it into chat.

Project description for the application: “ClaimGuard, Team Bug Eaters, IBM Z Datathon 2026 Track 01. We will run a Python/FastAPI synthetic healthcare-claim validation and Isolation Forest inference prototype on LinuxONE. No identifiable patient data or production insurer systems are involved.”

## Verify on the assigned VM

Connect using the supplied SSH instructions, then record these outputs in a private evidence log; redact hostnames/usernames before sharing:

```sh
date -u
uname -m
cat /etc/os-release
python3 --version
```

Expected architecture for this target is s390x, but that alone does not prove IBM ownership: retain the event provisioning evidence too. Python 3.11+ is required by the pinned scikit-learn version. Confirm availability before installing anything. Dependency installation on s390x has not been tested; do not assume wheels exist.

## Install and run after transferring the source

Exclude `.env`, `.git`, `.venv`, `node_modules`, SQLite files, and credentials from the transfer. Create a fresh environment on the VM. From the repository root:

```sh
sudo apt-get install -y python3-venv python3-pip python3-sklearn python3-pandas python3-joblib
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install --only-binary=:all: -r requirements-linuxone-api.txt
python -m backend.ml.train
python -m pytest -q
EXECUTION_TARGET=IBM_LINUXONE python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Train on the target to match the installed runtime and capture the artifact checksum and package versions. If dependencies cannot install, preserve the installation log and stop: do not claim successful LinuxONE execution or silently substitute a local service.

Keep the service bound to loopback. From the local machine, use the event-approved SSH alias:

```sh
ssh -N -L 8000:127.0.0.1:8000 YOUR_ASSIGNED_ALIAS
```

Stop the local backend first so the tunnel can use local port 8000. The existing frontend defaults can then reach the remote API through the tunnel. No public unauthenticated API exposure is needed.

## Evidence to collect

- Provisioning record, architecture and OS output, Python and dependency versions.
- Model training output, artifact checksum, passing tests, and server startup log.
- `/health` output showing disk-loaded model and actual machine architecture; EXECUTION_TARGET is a configured label, not proof by itself.
- From a second terminal on the VM: `python -m scripts.verify_demo --output evidence/linuxone-verification.json`.
- The output must show genuine successful inference, 100 WebSocket claim events, persisted reviewer verification disposition, timing conditions, and measured results.
- Capture the dashboard showing the remote results through the tunnel. Keep local and remote evidence files separate.

Deployment and remote timing are verified in evidence/linuxone/linuxone-verification.json. The final recorded presentation and official submission remain pending.

## Verified installation adjustment

The original pinned scikit-learn 1.8.0 installation had no compatible binary wheel on this VM; the failure is retained in evidence/linuxone/install.log. The working target uses Ubuntu-native scientific packages and a separate API dependency profile:

```sh
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip python3-sklearn python3-pandas python3-joblib
python3 -m venv --system-site-packages .venv
.venv/bin/pip install --only-binary=:all: -r requirements-linuxone-api.txt
.venv/bin/python -m backend.ml.train
.venv/bin/python -m pytest -q
EXECUTION_TARGET=IBM_LINUXONE .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Target versions: scikit-learn 1.4.1.post1, NumPy 1.26.4, SciPy 1.11.4, Joblib 1.3.2, Pandas 2.1.4+dfsg. The model was retrained on this target and its version contract matches the target runtime. Do not copy the Windows-trained artifact to it. Full versions and checksum are saved with the evidence. Tests passed with one Starlette/httpx test-client deprecation warning.

The API is now supervised by the enabled claimguard.service systemd unit and remains on loopback. An approved HTTPS proxy provides public access to the Vercel app, so no local SSH tunnel is required. The approved web-port restoration unit is enabled. Process-failure recovery passed; a whole-VM reboot was not performed. See PUBLIC-HOSTING.md for current operations. Keep the key outside transfers; *.pem is ignored by Git.

The final measured run reused seeded stream profiles from a prior run in the same remote database; duplicate findings increased REVIEW routing (94 REVIEW, 6 CORRECTION). These category counts are not accuracy results. The serial HTTP workload used unique synthetic patients. Remote HTTP timings are loopback on the VM and exclude the user's internet/SSH-tunnel round trip.