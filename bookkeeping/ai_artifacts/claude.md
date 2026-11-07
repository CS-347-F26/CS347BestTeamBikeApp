# Bike Transit Map — Project Context

This file brings Claude up to speed on the app. Claude reads it at the start of every session (a personal memory on Kenzie's machine points here). Read it before doing anything else, and ask before making decisions it lists as open. Keep it current: when the team makes a decision or the plan changes, update this file.

## What this is

A group final project for CS 347 (web development, Django-based course) by a team of four students. The app idea comes from Dr. Bowers, a faculty member, who will help test it.

The idea: organize a town's bike routes the way a transit system organizes its lines, displayed as a simplified, color-coded map in the style of the London Tube / DC Metro map. A cyclist should be able to think "I'm on the Red line, I need to switch to the Green line at this intersection" instead of reading a dense street map.

The first target town is Harrisonburg, VA. If it works, it should be easy to set up for other cities, so don't hard-code Harrisonburg-specific data into the logic.

## Why it matters

- People don't ride because they don't know a safe way to get where they're going (e.g., "how do I get across Route 42?").
- More people would ride if there were a published, cyclist-approved "here's how you can get around" map.
- Bigger cities have bike maps, but there's no good transit-style app for bike routes.
- Harrisonburg's existing bike map shows every road — too much information. Keep the display simple and abstracted.

## Users

1. **Map designer / city planner** — builds the transit-style map on top of the city: defines lines, colors, and stops/transfer points. Could eventually publish the map and print matching colored signage.
2. **Cyclists** — view the map, plan trips, and give feedback on where they feel safe or unsafe.

## Scope

### Version 1 (build this first)

Everything except live, real-time navigation while riding. That includes:

- Create named, color-coded route lines that follow real streets/paths.
- Define stations / transfer points where lines meet (intersections).
- Render the result as a **schematic tube-style map** (not a real street map in V1).
- View the published map and the list of routes.
- Plan a trip: the rider sees which routes and transfers get them from start to end. The directions are shown up front, not updated as they ride.
- Comments / feedback on routes, comfort ratings, and user accounts (see the data model below).

### Version 2 (later — don't build unless asked)

- Real-time navigation: track the rider's location and update upcoming turns, transfers and paths as they ride ("intersection for the Red line coming up").
- Spoken directions (text-to-speech).
- A real geographic street map view alongside the schematic one.
- Hazard reports for temporary issues (e.g., loose dogs).
- Alternative routes shown with different line styles (e.g., dashed for gravel).
- City-planning export: aggregated data planners can use.

## Data model (source of truth: the whiteboard)

The team's whiteboard diagram (`bookkeeping/images/DataModel.jpeg`) is the source of truth. The team expects it is incomplete and will add or remove things over time; start from it and change it as needed, but ask before large changes.

- **User** — id, username, password, prev_routes, saved_routes, marked_locations, comfortability (int)
- **Routes** — id, color, start_location, end_location, up_votes, down_votes, comments, marked_locations, comfortability (int)
- **Locations** — id, name, latitude, longitude, comment
- **Comments** — id, text, user_id, up_votes, down_votes

Relationships on the board: users ↔ routes is many-to-many; routes ↔ locations is many-to-many; routes have many comments; locations have many comments.

How it's implemented in `webapp_files/catalog/models.py` (decided 2026-11-03):

- `User` extends Django's `AbstractUser` (hashed passwords, built-in login); `AUTH_USER_MODEL = 'catalog.User'` in settings.
- `Route` has an extra `name` field (e.g. "Red Line") not on the board.
- Comments link to their route or location with foreign keys on `Comment` (`route.comments`, `location.comments`), rather than comment fields on Route/Location.
- All models use Django's automatic integer `id`.

Ideas from elsewhere that are **not** yet adopted (raise them when relevant, don't add them unasked):

- `bookkeeping/ai_artifacts/navigation-plan.md` proposes `is_station` on locations plus `segments` and `steps` tables.
- Segment attributes Dr. Bowers cares about: high vs. low traffic, bike lane or not, neighborhood vs. main road, surface type.

## Codebase layout

- `webapp_files/` — the Django project root (run commands from here).
  - `biketransit/` — project settings and root URLs.
  - `catalog/` — the main app. Keep the name `catalog`.
- `bookkeeping/` — notes, claims rubric, sketches, and AI files (`bookkeeping/ai_artifacts/`).
- `README.md` — the course project plan (narrative, features, claims).
- `bookkeeping/claims.md` — the grading rubric. Basic claims B10–B121 are required; the README lists the intermediate and stretch claims the team is aiming for.

## Tech stack & environment

- Django 6.1 on Python 3.14.
- **uv** for environments and dependencies. Always use `uv run python manage.py ...`, `uv add <pkg>`, etc. — never bare `python`/`python3` or `pip`.
- Note: `uv init` does not create `.venv`; it's created on first `uv add` / `uv sync` / `uv venv`.
- Secrets/settings come from environment variables, loaded from `webapp_files/.env` by `python-dotenv` (git-ignored; copy `webapp_files/.env.example`). `DJANGO_SECRET_KEY` is required; `DJANGO_DEBUG=True` turns debug on (off by default); `DJANGO_ALLOWED_HOSTS` is a comma-separated list of domains (defaults to `localhost,127.0.0.1`). The old hard-coded key is in git history, so treat it as public and never use it in production.
- Deployment: a Google Cloud VM running Docker Compose + Caddy, domain `mrossiter.me` (it already hosts other course projects as subdomains). This app will be deployed there too (Kenzie's copy: `bikeapp.mrossiter.me`), so keep it Docker-friendly and configure secrets/settings via environment variables.
- Each team member hosts their own copy on their own subdomain, so never hard-code a domain; per-deployment settings like `DJANGO_ALLOWED_HOSTS` go in that deployment's `.env`.
- Site-wide templates (`404.html`, `500.html`, `registration/login.html`) live in `webapp_files/templates/` (listed in `TEMPLATES["DIRS"]`); app templates currently sit flat in `catalog/templates/` (e.g. `route_detail.html`). The custom 404/500 pages only show when DEBUG is off (rubric B60).

## URL scheme (decided 2026-11-07, rubric B80)

- The app is mounted at `/bike-routes/` (the Python app folder stays `catalog`); `/` redirects there. Login/logout use Django's built-in auth at `/accounts/`.
- RESTful conventions: plural lowercase-hyphenated nouns, numeric `<int:pk>` ids (no slugs), sub-pages nested under their parent, trailing slashes. One URL for a form's GET and POST.
- Current map (URL names in parentheses): `routes/` (`route-list`), `routes/<pk>/` (`route-detail`), `routes/<pk>/feedback/` (`feedback-form`), `routes/<pk>/feedback/thanks/` (`feedback-confirmation`), `routes/<pk>/complete/` (`post-ride-feedback-prompt`), `feedback/` (`feedback-route-selection`), `locations/` and `locations/<pk>/`, `map/`, `trips/new/` (`trip-new`), `profile/` (login required).
- Always link with `{% url 'name' %}` / `reverse()` / `get_absolute_url`, never hard-coded paths. `UrlRoutingTests` in `catalog/tests.py` pins the paths; update it when adding a URL.

## Git workflow

- All four teammates work on the `development` branch for now.
- Merge to `main` only once the team is confident in V1 (or V2).
- Ownership of parts hasn't been decided yet.

## Open decisions (ask the team before choosing)

- Map/rendering library for the schematic view (e.g., pure SVG vs. Leaflet vs. MapLibre).
- Where street geometry comes from (City of Harrisonburg GIS and OpenStreetMap are candidates).
- Whether to use GeoDjango/PostGIS or store simple coordinates / GeoJSON.
- Database (SQLite for dev vs. Postgres).
- How the schematic layout is produced (manual placement vs. automated).
- Auth/roles for designers vs. riders.

## Working style

- This is a student group project — explain non-obvious choices briefly so the team can learn from and maintain the code.
- Keep V1 small and working before adding features.
- Make small, reviewable changes; don't restructure large parts of the project without asking.
- Views that look up one object by id use `get_object_or_404` (or a generic `DetailView`), so a missing id shows the 404 page instead of crashing with a 500. Add a test for the missing-id case.

## Reference links

- Harrisonburg bike map: http://harrisonburgva.gov/bike/map
- Local road-bike routes: https://www.rocktownbicycles.com/road-bike-routes
