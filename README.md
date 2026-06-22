b_connect_take_home_assignment

// project overview

Full stack app that simulates integration with a third party Wi-Fi controller API, My submissiion for the b_connect junior fullstack developer role, a applicaton where we can see the activity and monitor wifi access and activity, Fastapi backend app that is integrated with a third party wifi contoller getting information from the wifi endpoint and exposing it to our frontend react app to show wifi usage most active venues active session, times the wifi is most used and the age and gender that uses the wifi more, This app serves as a dashboard for devs management and stakeholders giving us a clear overview of usage activity, integrating our fastapi backend with thisrd party wifi controllers and creating our own api layer gives us controll over audit logs and session timeout, giving us a clear understanding of how the endpoint are being used and when and why there are faultys so we can fix the quicker and more effectively

// Tech Stack

Python Fastapi Https Httpx Uvicorn Supabase Postgres React Tailwind Vite Vercel

// Planning process

The plan for this project seems easy in my mind but i know it will take some architecture,firstly getting the data to work with, the options stated are interesting, i can create a json file wit a data payload mimicking how real data for a wifi controller might work but thats not interesting, bumped into a wifi controller api documentation that i can use and call to get the data called https://www.mywifinetworks.com/developers the api endpoint macth the project scope and it also gives me room to practice how it feels like to work and integrate with a real wifi controller endpoint, after i have the enpoint data using python build in https module, I will the use my FastApi application and create our api layer and wrap the api data from mywifinetwork into our own api endpoints, wrapping a third part api into our own api endpoint seems redundant but it gives us a clear understanding of our data and logs,uvicorn server runing on port 8000 to expose the api endpoint to our frontend to retrieve the data and create a real tmie interactive dashboard, supabase pstgress data base for data capturing and audit logs have 2 tables user_information to staore users info login start and end time gender mac_address for uuid and audit_logs for devs telling us which endpoint was triggered thhe httpx status so we know if the call was a success or error from which device and path, simple react frontend with two toggles management and devs, management page shows the data from the user_information table giving a clear understanding of client data and wifi controller activity read only, add an ai agent using openai sdk that management can text in plain englis and it then queries the database with any information, dev page has all the data from the audit_log table giving devs a backend understanding of the app what errors we facing have a soc analyst agent that analysis the logs for any errors and pings devs upoan any failed api log,

// Goal My goal is to complete this project and to end and that will be able to be done with the help of AI i will be using gemini pro for planning, give it my read me and the documentation ill be using so it has a clear understanding of my architecture and thought process have it write a plan.md file, the plan is to use AI as my pair programming buddy writing the code for all this manually is a super power that not most devs have latelly which i dont mind doing but a good developer knows how to leverage the speed of AI to their advantage being able to porpoerly instruct AI and give it a clear context while you have the foundation and fundamentals of programing makes you a good software engineer

// Achievements & Decisions

This section is my running log of what I actually shipped, where I deviated from the plan above, and why. The planning notes above are my original thinking; this section is how that thinking met the 2-3 hour time box and real production constraints. I'm keeping both so you can see the gap between plan and delivery and how I closed it.

What I finished

Designed the mock controller payload (mock_data.json) as a nested venues -> access points -> sessions structure: 2 venues, 4 access points (each with a unique MAC), and 12 sessions including start/end times, data usage, and age/gender demographics.

Designed the relational schema (schema.sql): venues, access_points, sessions, and sync_logs, with UUID primary keys, created_at/updated_at on every table, foreign keys, and a unique constraint on the access point MAC address so repeated syncs don't create duplicate hardware records.

Why I changed my initial plan

Real external API -> local JSON mock. My plan was to call the live mywifinetworks.com controller. For a prototype that needs to demo reliably I mocked the payload locally instead — this matches the brief's own first suggestion (a static JSON file) and removes a third-party dependency that could be down during review. I kept the payload realistic so swapping in a real controller later is a small change.

Two AI agents -> one focused insight feature. I originally wanted a management NL-to-SQL agent and a SOC-analyst log agent. The brief asks for a single optional AI feature, only after the core works, and warns against over-engineering inside a 2-3 hour box. I scoped down to one venue-operator insights feature so the core integration is solid first.

Added an audit/debug surface. The plan's audit-log instinct stays, folded into sync_logs (status, timing, record counts, errors) so the dashboard can show real sync status as the brief requires.

What's next

Build the FastAPI ingestion layer: POST /sync (idempotent ingest of the mock payload), GET /venues, GET /sessions, GET /sync-status, with basic error handling.

Drive the database through SQLAlchemy models (the brief prefers an ORM); schema.sql stays as the reference/migration target on Supabase Postgres.

Build the React dashboard: trigger sync, list venues/sessions, loading + error states, last-sync status.

If time allows: the single venue-operator AI insight feature, plus storing the raw provider payload for debugging. 

# SETUP INSTRUCTIONS

Prerequisites: Python 3.11+, Node.js 18+, and a Supabase (or any Postgres) database.

1. Database

Run Backend/schema.sql against your Postgres database (Supabase SQL editor or psql) to create the tables. The app does not auto-create tables — schema.sql is the source of truth and the SQLAlchemy models map onto it.

2. Backend

    cd Backend
    python -m venv .venv
    .venv\Scripts\activate          (Windows)   |   source .venv/bin/activate   (macOS/Linux)
    pip install -r requirements.txt
    cp .env.example .env             then set DATABASE_URL (and OPENAI_API_KEY for the AI features)
    uvicorn app.main:app --reload

API runs at http://localhost:8000 (docs at /docs).

3. Frontend

    cd Frontend
    npm install
    npm run dev

Dashboard runs at http://localhost:5173. It calls the backend at http://localhost:8000 by default; override with a Frontend/.env containing VITE_API_URL if needed.

4. First run

Open the dashboard and click "Sync Data" to ingest the mock controller payload — venues, sessions, and sync status will populate.

// API Endpoints

http://localhost:8000/docs

GET  /                health check
POST /sync            triggers a sync and ingests the controller payload (add ?simulate_failure=true to test the error path)
GET  /sync-status     the most recent sync run (status, timing, record counts), or null if none has run
GET  /venues          all venues with their nested access points
GET  /sessions        paginated sessions, supports limit, offset, active_only and venue_id query params
GET  /insights        AI-generated 3-bullet summary of current network activity
POST /chat            interactive AI assistant, takes a message and answers using read-only database tools

