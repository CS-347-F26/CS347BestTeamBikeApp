# Manual Accessibility Testing (Claim I89)

This document records the manual accessibility (a11y) testing of BikeWay for rubric claim **I89: Application passes manual a11y testing**. It covers what was tested, the issues found, the changes (and commits) that fixed them, and the final results.

## 1. Tool and setup

| Item | Value |
| --- | --- |
| Tool | [Accessibility Insights for Web](https://accessibilityinsights.io/docs/web/overview/), **Assessment** mode |
| Extension version | _TODO_ |
| Browser | Google Chrome _TODO version_ |
| Screen reader (for spot checks) | _TODO (e.g. VoiceOver on macOS)_ |
| Standard | WCAG 2.1 Level AA (what Assessment checks) |
| Site tested | _TODO (`http://localhost:8000` or `https://bikeapp.mrossiter.me`)_ |
| Branch / commit tested (Round 1) | `kenzie/a11y-testing` @ _TODO hash_ |
| Tester | _TODO_ |
| Round 1 date | _TODO_ |
| Round 2 date | _TODO_ |

Exported reports are saved in [`reports/`](reports/), named `round<N>-<page>.html` (for example `round1-login.html`).

### How a page was tested

1. Open the page in Chrome, start Accessibility Insights, and choose **Assessment**.
2. Run **Automated checks**, then go through each manual requirement group (Keyboard, Focus, Landmarks, Headings, Repetitive content, Links, Native widgets, Custom widgets, Timed events, Errors/status messages, Page navigation, Parsing, Images, Language, Sensory, Adaptable content, Pointer/motion, Semantics, Audio/Video, Multimedia, Live multimedia, Sequence, Visual helper). Mark each step Pass, Fail, or N/A (not applicable to the page).
3. Pages with forms are also tested in their error state (submit with missing or wrong data).
4. Save the result with **Export result** into `reports/`.

## 2. Pages tested

| # | Page | URL | Login needed | States tested |
| --- | --- | --- | --- | --- |
| 1 | Landing | `/` | No | default |
| 2 | Map | `/map/` | No | default |
| 3 | Routes | `/routes/` | No | default |
| 4 | Route detail | `/routes/<id>/` | No | default |
| 5 | Feedback (route list) | `/feedback/` | No | default |
| 6 | Feedback form | `/routes/<id>/feedback/` | Yes | default, error (no rating), thank-you popup |
| 7 | Locations | `/locations/` | No | default |
| 8 | Location detail | `/locations/<id>/` | No | default |
| 9 | Log in | `/accounts/login/` | No | default, wrong password |
| 10 | Sign up | `/signup/` | No | default, errors |
| 11 | Profile | `/profile/` | Yes | default |
| 12 | Edit profile | `/profile/edit/` | Yes | default, error |
| 13 | Change password | `/accounts/password_change/` | Yes | default, errors |
| 14 | Delete account | `/profile/delete/` | Yes | default |
| 15 | 404 page | any missing URL (with `DJANGO_DEBUG=False`) | No | default |
| 16 | Plan a trip | `/trips/new/` | No | default (placeholder page for now) |

## 3. Round 1 results (before fixes)

| # | Page | Report | Automated checks | Manual groups failed | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Landing | _TODO_ | _TODO_ | _TODO_ | |
| 2 | Map | _TODO_ | _TODO_ | _TODO_ | |
| 3 | Routes | _TODO_ | _TODO_ | _TODO_ | |
| 4 | Route detail | _TODO_ | _TODO_ | _TODO_ | |
| 5 | Feedback (route list) | _TODO_ | _TODO_ | _TODO_ | |
| 6 | Feedback form | _TODO_ | _TODO_ | _TODO_ | |
| 7 | Locations | _TODO_ | _TODO_ | _TODO_ | |
| 8 | Location detail | _TODO_ | _TODO_ | _TODO_ | |
| 9 | Log in | _TODO_ | _TODO_ | _TODO_ | |
| 10 | Sign up | _TODO_ | _TODO_ | _TODO_ | |
| 11 | Profile | _TODO_ | _TODO_ | _TODO_ | |
| 12 | Edit profile | _TODO_ | _TODO_ | _TODO_ | |
| 13 | Change password | _TODO_ | _TODO_ | _TODO_ | |
| 14 | Delete account | _TODO_ | _TODO_ | _TODO_ | |
| 15 | 404 page | _TODO_ | _TODO_ | _TODO_ | |
| 16 | Plan a trip | _TODO_ | _TODO_ | _TODO_ | |

## 4. Issues found and fixes

Each issue lists the WCAG success criterion it breaks, where it happens, what was changed, and the commit that fixed it.

| ID | Issue | WCAG criterion | Page(s) | Fix | Commit |
| --- | --- | --- | --- | --- | --- |
| A1 | _TODO_ | | | | |

## 5. Round 2 results (final)

| # | Page | Report | Automated checks | Manual groups failed | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Landing | _TODO_ | _TODO_ | _TODO_ | |
| 2 | Map | _TODO_ | _TODO_ | _TODO_ | |
| 3 | Routes | _TODO_ | _TODO_ | _TODO_ | |
| 4 | Route detail | _TODO_ | _TODO_ | _TODO_ | |
| 5 | Feedback (route list) | _TODO_ | _TODO_ | _TODO_ | |
| 6 | Feedback form | _TODO_ | _TODO_ | _TODO_ | |
| 7 | Locations | _TODO_ | _TODO_ | _TODO_ | |
| 8 | Location detail | _TODO_ | _TODO_ | _TODO_ | |
| 9 | Log in | _TODO_ | _TODO_ | _TODO_ | |
| 10 | Sign up | _TODO_ | _TODO_ | _TODO_ | |
| 11 | Profile | _TODO_ | _TODO_ | _TODO_ | |
| 12 | Edit profile | _TODO_ | _TODO_ | _TODO_ | |
| 13 | Change password | _TODO_ | _TODO_ | _TODO_ | |
| 14 | Delete account | _TODO_ | _TODO_ | _TODO_ | |
| 15 | 404 page | _TODO_ | _TODO_ | _TODO_ | |
| 16 | Plan a trip | _TODO_ | _TODO_ | _TODO_ | |

## 6. Known limitations

_TODO: anything left that can't be fully fixed, and why (for example, panning the map needs a drag; the zoom buttons, arrow keys and the text list of routes and places are the alternative)._
