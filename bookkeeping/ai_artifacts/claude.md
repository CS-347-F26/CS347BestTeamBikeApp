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
- **Waypoints** (added 2026-11-10): markers along routes. `Waypoint` has notes, latitude, longitude, likes, dislikes, and `routes` (many-to-many). The waypoint's order (0-based index from start to end of a route) lives on the through model `RouteWaypoint` (route, waypoint, order), because one waypoint can be on several routes at different positions. `route.route_waypoints` returns them in order; order and waypoint are each unique per route.

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

## URL scheme (updated 2026-11-12, rubric B80)

- Bike Transit pages are mounted at the domain root (the Python app folder stays `catalog`). `/` is the welcome landing page, `/home/` is the app home, and the navigation's Home link returns to `/`. Login/logout use Django's built-in auth at `/accounts/`.
- RESTful conventions: plural lowercase-hyphenated nouns, numeric `<int:pk>` ids (no slugs), sub-pages nested under their parent, trailing slashes. One URL for a form's GET and POST.
- Current map (URL names in parentheses): `routes/` (`route-list`), `routes/<pk>/` (`route-detail`), `routes/<pk>/feedback/` (`feedback-form`), `routes/<pk>/feedback/thanks/` (`feedback-confirmation`), `routes/<pk>/complete/` (`post-ride-feedback-prompt`), `feedback/` (`feedback-route-selection`), `locations/` and `locations/<pk>/`, `map/`, `trips/new/` (`trip-new`), `profile/` (login required).
- Always link with `{% url 'name' %}` / `reverse()` / `get_absolute_url`, never hard-coded paths. `UrlRoutingTests` in `catalog/tests.py` pins the paths; update it when adding a URL.

## Styling / CSS (decided 2026-11-12)

- **Mobile first.** Most riders will use a phone, so each page is designed and built for a phone (~375px wide) first. Desktop changes are added later in `@media (min-width: 48rem)` blocks.
- **Bootstrap is used only where the team picks it.** Bootstrap **5.3.3** (CSS and the JS bundle) is loaded from a CDN in `base_generic.html`. Use only the Bootstrap components Kenzie links for a page; everything else is our own CSS. Stay on 5.3 even when a link points to the Bootstrap 6 docs (6.0 is an alpha); use the matching 5.3 page (`getbootstrap.com/docs/5.3/...`).
- **Nav** (decided 2026-11-12, applies to every page): a top bar with a hamburger (three lines) on the left. Tapping it slides a dark-teal panel in from the left (Bootstrap offcanvas, `offcanvas-start`, with an X to close) holding a vertical pill nav (`nav nav-pills flex-column`); the current page is the filled pill. Same on desktop for now.
- **Home goes to the landing page for now** (decided 2026-11-12): the Home links in the hamburger and the bottom bar point to `landing` (`/`), not `index`. `index.html` and its URL (`/home/`) are kept but nothing in the nav links to them.
- **Landing page** (`landing.html` + `pages/landing.css`): only the centered BikeWay title, the "Bike Riding Your Way." tagline and the welcome paragraph, in dark teal on the app's pale sage background. Kenzie tried a dark-teal page with white text and rejected it.
- **Shared route rows** (`pages/route-rows.css`, 2026-11-12): the full-height page, the centered `.page-title-band` (was `.routes-header`), the edge-to-edge `.route-rows` stack, and the base `.route-row` (colors come from `.route-color--<color>` in `main.css`). Used by the routes page and the feedback page; each adds its own row layout (`routes.css`, `feedback.css`). Like `auth.css`, it's a shared page file rather than `main.css` because of the full-height rules.
- **Route colors are shared** (2026-11-12): `.route-color--<color>` classes at the end of `main.css` set `--route-bg` (light tint) and `--route-ink` (darker shade). Put `route-color--{{ route.color|lower }}` on any element (rows, or the page `<body>` via `{% block body_class %}` in `base_generic.html`). To support a new route color, add one line there. (They used to be `.route-row--<color>` in `route-rows.css`.)
- **Feedback form page** (`feedback_form.html` + `pages/feedback-form.css`, `feedback-form` URL, 2026-11-12; built and checked with Red, works for any color): the whole page is the route's tint, with the route name large and centered in the dark shade under a small "Give feedback" line. A white card holds the comfort rating (five tappable 1–5 squares that are real radio buttons, "Very uncomfortable" to "Very comfortable"), an optional Comments box, and a centered "Submit feedback" button. **Login required.** `RouteFeedbackForm` (in `forms.py`) saves a `RouteFeedback` with the user and route, then redirects back to the same page with a one-time session flag, which opens a Bootstrap modal: smiley, "Feedback received!", "Thank you for your feedback.", "Back to routes" and Close. The old `feedback-confirmation` page still exists but the form no longer goes there.
- **Profile page** (`profile.html` + `pages/profile.css`, 2026-11-12, designed by Claude): white cards on sage. The header card has an initial avatar, username, "Member since", and three stat tiles (Comfort level `n/5` or "Not set", Feedback given, Saved routes). Then cards for Saved routes (rows in each route's tint and dark shade), Your recent feedback (latest 3, with a left bar in the route's dark shade), Previous rides and Marked locations, each with an empty state. An Account card holds Edit profile (primary) and Change password (outlined), and a separate dark-red "Delete account" link sits at the bottom. The `profile` view passes `recent_feedback` and `feedback_count`. Edit profile (`profile_edit.html`), delete-confirm (`profile_confirm_delete.html`, a dark-red danger button with a warning box) and change password (our own `templates/registration/password_change_form.html` / `password_change_done.html`, overriding Django's admin-looking defaults, with Show/Hide on all three fields) use the same white card from `auth.css`, with a full-width main button and an outlined Cancel back to the profile.
- **Feedback page** (`feedback_route_selection.html` + `pages/feedback.css`, 2026-11-12): a "Feedback" title band ("Pick a route to tell us how it felt."), then the same color rows, each one big link with the route name centered in its darker shade and a › chevron on the right. A row opens that route's `feedback-form`. The view now passes `route_list`; the `{% empty %}` block shows 6 example rows (links to ids 1–6, which 404) until real routes exist.
- **Routes page** (`route_selection.html` + `pages/routes.css`, 2026-11-12): a centered "Routes" title band, then full-width stacked rows, one per route, each with three columns: name | comfort rating (1–5) | Comments button (links to `route-detail` for now). Each row's background is a light tint of the route's color and the name is a darker shade of it, set by `.route-color--<color>` classes (in `main.css`) keyed on `route.color|lower` (red, yellow, black, purple, blue, green, plus orange, pink and maroon for the official Harrisonburg routes; add a class for a new color). While the database has no routes, the template's `{% empty %}` block shows 6 hard-coded example rows; delete it once real routes exist.
- **Card-style form pages** (login, sign up, edit profile, delete account, change password and its done page) share one stylesheet, `pages/auth.css` (`.auth-card`, `.auth-field`, `.auth-submit`, ...), and one script, `catalog/static/catalog/js/password-toggle.js`, which powers every `.password-toggle` button. They share a page file instead of moving to `main.css` because the full-height centering rules would affect every page.
- **Sign-up page** (`templates/registration/signup.html`, 2026-11-12): the same card as login, titled "Create your account", with Show/Hide on both password fields, Django's help text under each field in slate, and field errors in dark red right under the field. It links back to Log in.
- **Login page** (`templates/registration/login.html`, 2026-11-12, designed by Claude and approved by Kenzie): a white card centered between the bars on the sage background, with "Welcome back", visible labels, 48px inputs with 16px text, a Show/Hide password button (hidden without JS), a full-width dark-teal "Log in" button, and a "Create an account" link. No colored stripe on the card (Kenzie rejected it). On a failed login, `StyledAuthenticationForm.get_invalid_login_error` in `catalog/forms.py` marks both fields `aria-invalid` and links them to the `#login-error` message.
- **Bottom tab bar** (built 2026-11-12, every page, alongside the hamburger): fixed to the bottom with Home, Map, Routes and Log in, each an icon with a small label under it. When logged in, Log in becomes Profile (same icon); Log out stays in the hamburger. The current page is yellow. Icons are inline SVG snippets in `catalog/templates/icons/` (`{% include "icons/home.svg" %}`) with `fill="currentColor"` so CSS sets their color. Kenzie downloaded them (the home icon is from SVG Repo); check each icon's license before publishing and credit it if required.
- **One page at a time.** For each page, Kenzie provides a drawing of the mobile layout and links to the Bootstrap components to use. Build that page to match, check it at mobile size, then review it before moving on. Don't style a page before its drawing arrives, and ask if the drawing is unclear.
- **Files** (in `catalog/static/catalog/css/`):
  - `main.css`: everything shared, in four commented sections: variables (colors, route-line colors, spacing, fonts), tag defaults, the app shell (header/main/nav), and shared pieces.
  - `pages/<page>.css`: one per page, created when that page is styled.
- **Colors** (decided 2026-11-12, variables at the top of `main.css`): dark teal `#084C61` is primary (header, tab bar, main buttons, headings, text); slate `#4F6D7A` is secondary; yellow `#E3B505` is the accent (never as text on white); light teal `#56A3A6` is positive/success; red `#DB504A` is danger; the page background for the whole app is pale sage `#D1E2DF` (changed from off-white 2026-11-12; dark teal text on it is 7.1:1, but slate is only 4.1:1, so keep slate text bold/large). Rules use the role variables (`--color-primary`, etc.). Keep red and yellow to small accents so the routes' own line colors stand out on the map.
- A style starts in its page file. When a second page needs it, it moves to the shared-pieces section of `main.css`.
- Load order in `base_generic.html`: Bootstrap, then `main.css`, then `{% block page_css %}`, so our CSS overrides Bootstrap. A page adds its file with `{% block page_css %}<link rel="stylesheet" href="{% static 'catalog/css/pages/<page>.css' %}">{% endblock %}` (the template needs `{% load static %}`). `{% block extra_head %}` stays for other head content, like the map page's MapLibre CSS.

## Git workflow

- All four teammates work on the `development` branch for now.
- Exception (2026-11-12): Kenzie's styling work lives on its own branch, `kenzie/styling` (tracks `origin/kenzie/styling`), and gets merged into `development` when a page is ready. A plain `git push` works on it.
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
