# MediBridge AI

**Right Care, Less Waiting, Better Access** · HackShift 2026 · Silent Revolution

MediBridge AI is a local demonstration application for family health and clinician workflows. The public landing page leads to separate patient and doctor sign-in experiences. React communicates with the Flask REST API; Flask stores demo data in SQLite under `backend/database/medibridge.db`.

## Project Structure

```text
medibridge/
├── frontend/
│   ├── src/
│   │   ├── components/       # Shared navigation and emergency dialog
│   │   ├── context/          # Authentication and English/Hindi preferences
│   │   ├── pages/            # Landing, role logins, family and doctor screens
│   │   ├── layouts/          # Protected application shell
│   │   ├── services/api.js   # Centralized REST client
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── .env.example
│   └── package.json
├── backend/
│   ├── routes/               # Flask blueprints
│   ├── services/             # Triage, optional AI, and email utility
│   ├── database/             # SQLite connection, schema, and demo seeds
│   ├── tests/                # Isolated pytest integration tests
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
├── .gitignore
└── README.md
```

The SQLite file is created on first backend startup. Its absolute default location is derived from the backend source path, not the current working directory. Tests each use an independent temporary database.

## Requirements

- Python 3.11 or newer (tested here with Python 3.14)
- Node.js 20.19+ (tested here with Node 24 LTS) and npm
- VS Code or another editor
- Internet access only for downloading packages, optional AI requests, Google Fonts, and external Jitsi calls

## Configure and Start the Backend

Open a PowerShell terminal in VS Code:

```powershell
cd path\to\medibridge\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` before using outside a local demo. Set a private random `SECRET_KEY`. The checked-in example contains placeholders only. `.env` is loaded by the backend. Leave `MEDIBRIDGE_DATABASE` empty to use the stable default file at `backend/database/medibridge.db`.

Start Flask from the `backend` folder:

```powershell
python app.py
```

Backend URL: `http://127.0.0.1:5000`  
Health check: `http://127.0.0.1:5000/api/health`

## Configure and Start the Frontend

Open a second VS Code terminal:

```powershell
cd path\to\medibridge\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

`frontend/.env` can override the API base URL with `VITE_API_URL=http://127.0.0.1:5000/api`. Restart Vite after changing environment variables. The frontend reads the bearer token from `sessionStorage`; it never reads database credentials or AI keys.

If PowerShell blocks virtual-environment activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or invoke `.venv\Scripts\python.exe` directly. If `npm` is not recognized after installing Node, open a new terminal so Windows refreshes `PATH`.

## Demo Accounts

The backend idempotently seeds these fictional identities on startup:

| Role | Email | Password |
|---|---|---|
| Patient | `patient@medibridge.demo` | `DemoPatient123!` |
| Doctor | `doctor@medibridge.demo` | `DemoDoctor123!` |
| Demo admin | `admin@medibridge.demo` | `DemoAdmin123!` |

The seeded patient is explicitly assigned to the demo doctor. The demo doctor starts with `pending` verification and is omitted from patient doctor search until admin review. Sign in as the demo admin at `/admin/login` to review and set a status. New accounts and demo admin credentials are stored as Werkzeug password hashes. The demo login does not send or verify email.

## Run Tests and Build

From the repository root:

```powershell
cd backend
python -m pytest -q tests
cd ..\frontend
npm run build
```

The backend tests create a fresh temporary SQLite file and private upload directory per test fixture. They cover health and seeding, registration/login/hash storage, phone login, role restrictions and record privacy, pending doctor profile access, admin-only verification/status persistence, family ownership, private report upload/download validation, medication provenance and taken logs, chat persistence and triage stages, appointment acceptance, patient-doctor messaging, consultation approval, and bed booking references/cancellation.

## Implemented Workflows

- Patient and doctor registration/login, role-gated routes, signed bearer tokens, and client-side logout
- Public landing page with separate patient/doctor login; role-mismatch login is rejected by the backend
- Patient family dashboard with family profile create/edit/remove and owner-scoped medical details
- Patient overview, assigned doctor directory, appointment requests and status tracking
- Patient symptom chat with persisted multi-turn context, progressive follow-up questions, severity/duration collection, negation-aware warning signs, triage assessment storage, and immediate emergency escalation
- Browser voice input with editable English/Hindi transcripts, listening/error states, and unmount cleanup; user-controlled read-aloud with Play/Stop and speech cancellation
- Patient-doctor messages are available only after an accepted appointment/explicit assignment, use a stable ID-based conversation, persist in SQLite, and refresh by polling (no WebSocket/push service)
- Doctor dashboard, verification status, assigned patient list/history, private messaging, appointment actions, consultation draft/approval, and approved patient-facing reports
- Separate demo-admin review at `/admin/login`; only an admin token can change doctor status among `pending`, `verified`, and `rejected`, with reviewer notes and an audit trail
- Private PDF/PNG/JPEG uploads with family association, content-signature checks, 10 MB limit, and authenticated preview/download
- Medicine schedule with patient-entered versus doctor-prescribed records, reminder-time labels, taken logs, and completion state
- Searchable fictional doctor profiles and hospital/bed-type/cost demo filters
- Two-step bed request review with unique reference, pending/cancelled tracking, and no false reservation claim
- SOS confirmation, direct `tel:112` link, emergency instructions, and no ambulance-dispatch claim
- English/Hindi navigation/preferences and translated triage safety responses
- Optional OpenAI-compatible structured triage classification through backend-only environment settings
- Accepted appointment participants can request an external Jitsi demo room link from the API

## External Services and Safety Boundaries

- **AI:** Without `AI_API_KEY`, the application uses labeled rule-based conversational demo guidance. With an OpenAI-compatible key configured, the backend sends the current and recent conversation turns for structured urgency classification, validates the stage, never lowers locally detected urgency, and uses fixed safety guidance. The conversational follow-up templates remain rule-based; this is not a generative medical diagnosis service. Emergency symptoms bypass the remote call. Provider failures fall back to the demo. No API key is sent to React.
- **Email verification:** Not implemented in this build. Registration does not claim that an email was sent or verified. The SMTP settings in the example are placeholders for a future integration.
- **Doctor verification:** The fictional seeded doctor starts pending. Only the separate demo-admin workflow can change the persisted status; pending/rejected accounts can see their own profile but cannot use sensitive clinician endpoints. No external licensing/credential verification provider is connected.
- **Verification prototype:** The demo admin credentials are intentionally local prototype credentials. Status changes persist in SQLite, but neither the admin screen nor its `verified` label confirms real-world licensing, identity, or credentials. Do not deploy these credentials or treat client-side routing as production authorization.
- **Video:** The API returns a participant-authorized link to the external public Jitsi service after an appointment is accepted. The demo does not embed or verify a connected call; Jitsi requires internet, microphone/camera permission, and may be unavailable. The room is not a private clinical system. Do not share real patient information.
- **Hospitals and doctors:** All seeded providers and facilities are fictional. Bed counts are simulated, not live, reservations, or confirmed availability. A submitted bed request is an inquiry only.
- **Language coverage:** Navigation, core dashboard labels, selected controls, and assistant safety messages support Hindi. Some detailed form text and help copy remain English; translation coverage is not complete.
- **Production readiness:** This is a hackathon demo, not a medical device or production patient-record platform. Tokens are kept in browser session storage and are not server-revocable. Configure secrets, HTTPS, provider verification, audit controls, clinical governance, and a privacy/security review before any real use.

## Complete Demo Walkthrough

1. Start Flask in terminal 1 and Vite in terminal 2. Open `http://127.0.0.1:5173`; the landing page shows separate patient and doctor access cards.
2. Select **Patient Login**, sign in as `patient@medibridge.demo` with `DemoPatient123!`, and verify the patient family dashboard loads.
3. Open **My family**, add a family member with a relationship and optional health notes, then switch profiles and edit/remove the profile.
4. Open **Medical reports**, upload a PDF or image under 10 MB, associate it with a family member, then preview or download it. Uploads are private and require the signed-in patient session.
5. Open **Medicines**, add a patient-entered record, reminder times, and dates. Select the checkmark to mark a dose taken; the UI does not recommend medicines or send push notifications.
6. Open **Hospital bed booking**, search/filter mock hospitals and bed types, choose **Book bed**, enter a patient and date, review, then confirm. Record the reference and `pending-demo` status under **My bookings**; no real bed is reserved.
7. Open **Digital Healthcare Assistant** tabs to reach chat, reports, medicines, prescriptions, and health history. Send `severe chest pain` in the chat to see immediate 112 guidance.
8. Select **Doctor Login** and sign in as `doctor@medibridge.demo` with `DemoDoctor123!`. The profile shows as a verified demo doctor; patient accounts cannot open doctor routes.
9. As the doctor, accept the patient appointment request, inspect **My patients**, message the assigned patient, create a consultation draft, and approve it. Return to the patient account to see approved clinician records.
10. Use the header language selector to switch English/Hindi and reload to confirm the choice persists. Test the SOS button; it opens instructions and a `tel:112` link but does not dispatch an ambulance.
11. Restart Flask and verify profiles, uploads, medicine records, chats, appointments, and booking requests remain in SQLite. Run `python -m pytest -q tests` and `npm run build` for automated checks.

For automated checks, run `python -m pytest -q tests` in `backend`, then `npm run build` in `frontend`.
