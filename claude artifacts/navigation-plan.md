# Bike Transit Map: Navigation & Route Network Plan

Oct 27, 2026 · @Kenzie

## Summary

We will not use an outside turn-by-turn navigation tool. Riders pick a start and end **station** on our network, our own code finds a path over our vetted routes, and the app gives turn-by-turn directions along those routes ("In 300 ft, turn left onto Main St") plus route-level cues ("transfer to Green coming up").

This answers our professor's feedback on the plan: *"i can't tell how much turn-by-turn navigation you're planning to include and whether you will attempt to rely on an existing tool for that part."* The route network itself starts from the City of Harrisonburg's official bike map, then gets curated by us with Dr. Bowers.

## Option A: how navigation will work

Think of it like the DC Metro. Nobody expects the Metro to start at their front door: you go to a station, ride the lines, and get off at the station nearest your destination. Our app works the same way, so every part of every trip stays on a vetted route.

1. **Rider picks a start and end station.** They can tap one on the map, search a list, choose a saved place (home, class, work), or press "nearest station." Nearest station only needs the browser's GPS and a straight-line distance check, with no routing service.
2. **Our code finds the path.** The route network is stored as a graph: stations are nodes, route segments between them are edges. We run our own shortest-path search (Dijkstra algorithm) over it. Edge weights can include distance and each route's comfort rating, so riders with a low comfort level get gentler routes.
3. **The app turns the path into directions.** For example: "Start on Red at Memorial Hall → ride 4 stops → transfer to Green at Port Republic → arrive at Downtown." Each segment carries its stored turn steps (see step 5 of Building the route network), so the trip becomes an ordered list: turn instructions along Red, a transfer cue at Port Republic, turn instructions along Green, then arrival. No outside directions service is called during the ride.
4. **Live cues while riding.** The browser's Geolocation API (`watchPosition`) tracks the rider. Each GPS reading is snapped to the route line (Turf.js nearestPointOnLine) to find how far along the route the rider is. The app shows the next stored turn with the distance left ("In 300 ft, turn left onto Main St"), updates it as they ride, and gives a final cue just before the turn. Transfers and arrival work the same way: when the rider gets within about 100 m of their next transfer or their end station, the app shows a cue like "Transfer to Green coming up."
5. **Version 2: spoken cues.** The browser's built-in Web Speech API (`speechSynthesis`) reads turn instructions and transfer cues aloud. It is free, needs no account, and covers our text-to-speech claim.

**What we are NOT building:** directions to the first station (getting there is up to the rider, like walking to a subway stop) and automatic rerouting. If a rider leaves the network, the app shows "You've left the Red Route" and points them back to the nearest station.

**Why this is a good choice:** no API keys, no rate limits, no outside service that can go down during our demo, and the safety promise holds because riders never leave vetted routes inside the app.

## Options we considered

We looked at three levels of relying on outside tools and picked the one with no runtime dependency. If someone asks "why not just use Google Maps," this is the answer.

| Option | What it is | Cost | Why we didn't pick it |
| --- | --- | --- | --- |
| **A: Our own graph (chosen)** | Station-to-station routing on our vetted network | Free | — |
| B: Hybrid | Option A plus an outside cycling router (e.g. openrouteservice) to get riders from home to the nearest station | Free tier: 2,000 requests/day | The outside leg can send riders down unsafe streets, breaking our safety promise. Adds an API key, rate limits, and a service that can fail during the demo. |
| C: Full routing engine | Self-host GraphHopper or BRouter and bias it toward our routes | Free (open source) but needs a server | Running a Java server and importing OpenStreetMap data is too much infrastructure for one semester. |
| Commercial APIs | Mapbox Directions, Google Maps | Mapbox free up to 100,000 requests/month; Google paid | Vendor lock-in, and their bike routing optimizes for speed, which is the problem we're solving. |

**One trap to avoid:** many tutorials use Leaflet Routing Machine. Its author no longer maintains it, and it defaults to an OSRM demo server it says is not a reliable default. Don't build on it.

Option B stays available as a stretch goal later if we want first/last-mile directions. If we ever add it, the outside leg should be drawn as a dashed "unvetted connection" line and called from our backend so the API key stays private.

## Building the route network

We make the network ourselves, because "vetted" is a human judgment no API can make, but we start from the city's official bike map instead of a blank page. Tools do the tedious tracing.

1. **Study the city's bike map.** The [Harrisonburg Community Bike Map](https://harrisonburgva.gov/bike-map) was made by the City with JMU and rates streets with a "cycling comfort level" based on a Mineta Transportation Institute low-stress bicycling method. That is very close to our comfort score, so we should read how they rate streets and cite it.
2. **Pull the city's GIS data.** The City runs a public ArcGIS server with layers like [recommended bicycle lanes](https://gis.harrisonburgva.gov/arcgis/rest/services/PublicWorks/PWPlanningDatasets/MapServer/14/iteminfo) and [city streets](https://gis.harrisonburgva.gov/arcgis/rest/services/DataHub/City_Streets/MapServer/0/iteminfo). ArcGIS layers can usually be exported as GeoJSON through a `/query?where=1=1&outFields=*&f=geojson` URL. We have not yet confirmed which layer holds the comfort ratings or whether it is public, so do this first.
   - Backup source: [overpass-turbo.eu](https://overpass-turbo.eu) can export every OpenStreetMap bike lane, path, and trail in Harrisonburg as GeoJSON for free.
3. **Load it as a reference layer.** Open the GeoJSON in [geojson.io](https://geojson.io) (free, in the browser) so we can see existing bike infrastructure on a real map.
4. **Choose the routes with Dr. Bowers.** Pick about 4–6 color-coded routes that cover campus, downtown, and the main neighborhoods. Use the city's comfort levels as a starting point, then adjust with local knowledge (shortcuts, hills, mean dogs).
5. **Draw each route.** In geojson.io, click waypoints along each route and name it ("Red Route"). To make lines follow the actual streets instead of tracing curves by hand, run the waypoints once through a router like openrouteservice or the OSRM demo. The same response includes turn-by-turn steps for the route (an instruction like "Turn left onto Main St", its distance, and where along the line it happens). Save those into the steps table and read through them, since street names come from OpenStreetMap and may need fixing. All of this happens only while we build the network, so riders never depend on it.
6. **Add stations.** Put a station everywhere two routes cross (transfer points) and at popular destinations: campus buildings, downtown, grocery stores, parks. Too few stations means long rides just to reach one.
7. **Turn the lines into a graph.** A short script uses Turf.js `lineIntersect` to find crossings, splits routes into segments between stations, and saves nodes (stations) and edges (segments with distance and comfort rating) to our database.
8. **Test it.** Run a handful of real trips (a dorm to downtown, a grocery store to campus) and confirm every station can reach every other one. Then walk or ride each route once with the app to check that turn instructions make sense and fire at the right time.
9. **Optional: an in-app route editor.** Leaflet-Geoman lets an admin like Dr. Bowers draw and edit routes inside our app and save them to the `routes` table. That's real CRUD and lets the network grow after the class ends.

**Attribution:** if we use OpenStreetMap data we must show OSM attribution on the map, and we should credit the City for its data.

## Changes to our plan

This approach needs a few small updates to the data model, sketch, and claims.

**Data model**

- `locations` gets an `is_station` boolean (bool). Stations are just locations riders can start or end at.
- New `segments` table for the graph's edges: `id` (int), `route_id` (int, FK → routes), `from_location_id` (int, FK → locations), `to_location_id` (int, FK → locations), `distance_m` (float), `geometry` (GeoJSON string).
- New `steps` table for turn-by-turn instructions: `id` (int), `segment_id` (int, FK → segments), `instruction` (str, e.g. "Turn left onto Main St"), `maneuver` (str: left, right, straight), `distance_m` (float), `position_m` (float, how far along the segment the turn happens).
- `routes` keeps `color` and `comfortability`, plus a `geometry` (GeoJSON string) for drawing the line.
- Relationships: a route has many segments; a segment has many steps; each segment connects two locations; a location can be on many routes (that's what makes it a transfer station).

**Sketch (each screen needs a URL)**

| Screen | Possible URL | Signed in? |
| --- | --- | --- |
| Landing map | `/` | No |
| Route list | `/routes` | No |
| Route comments | `/routes/:id` | No (read), Yes (write) |
| Plan a trip: pick start and end station (new screen) | `/plan` | No |
| Active ride with cues | `/ride/:tripId` | No |
| Give feedback | `/routes/:id/feedback` | Yes |
| Account and comfort level | `/account` | Yes |

**Claims this supports**

- I20 search: searching stations by name on the plan-a-trip screen.
- Text-to-speech: Web Speech API for spoken cues (Version 2).
- I90 mobile-responsive: the ride screen is mainly used on phones.
- I60 import/export: a shareable trip link like `/plan?from=12&to=31` fits naturally.

## Wording for the plan and open questions

Paste this into the Features section of our README to answer the feedback directly:

> **Navigation.** Riders choose a start and end station on our network, and the app computes a path over our vetted-route graph using our own implementation of Dijkstra's algorithm. While riding, the app gives turn-by-turn directions along the vetted routes (e.g. "In 300 ft, turn left onto Main St") plus cues for transfers and arrival, based on the rider's GPS position. Turn instructions are generated once with openrouteservice when we build each route and stored in our database, so no outside navigation service is used during rides. Version 2 reads directions aloud using the browser's built-in Web Speech API. We will not give directions to the first station (riders get there on their own, like walking to a subway stop) or reroute riders who leave the network. The route network is curated by our team with Dr. Bowers, using the City of Harrisonburg's Community Bike Map as a starting point.

**Open questions**

- [ ] Which city GIS layer holds the comfort ratings, and can we export it as GeoJSON?
- [ ] Does Dr. Bowers want to choose the routes directly or review ones we propose?
- [ ] How many routes and stations do we aim for in version 1?
- [ ] Do we build the in-app route editor, or just load routes from GeoJSON files?
- [ ] Feet or meters for distances in turn instructions?
- [ ] What exactly happens when a rider leaves the route: a warning only, or a pointer back to the nearest station?
- [ ] How early should turn cues fire, given phone GPS is often off by 5–10 m?
- [ ] Who owns each piece: data import, graph and pathfinding, ride screen and cues?

## Tools and sources

| Tool | Used for | Cost |
| --- | --- | --- |
| [Harrisonburg Community Bike Map](https://harrisonburgva.gov/bike-map) | Starting point for routes and comfort levels | Free |
| [Harrisonburg GIS server](https://gis.harrisonburgva.gov/arcgis/rest/services/PublicWorks/PWPlanningDatasets/MapServer/14/iteminfo) | Bike lane and street data as GeoJSON | Free |
| [overpass-turbo](https://overpass-turbo.eu) | Backup: OpenStreetMap bike data export | Free |
| [geojson.io](https://geojson.io) | Drawing and editing route lines | Free |
| [openrouteservice](https://openrouteservice.org/?p=176) | One-time snapping of routes to streets and generating turn instructions (2,000 requests/day free) | Free |
| Turf.js | Finding route intersections, snapping rider GPS to the route, distance to next turn | Free, open source |
| Leaflet + Leaflet-Geoman | Displaying the map; optional route editor | Free, open source |
| Geolocation API / Web Speech API | Rider position; spoken cues | Built into browsers |

Other sources: [openrouteservice terms (OSM attribution)](https://openrouteservice.org/?p=940) · [OSRM demo server policy](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server) · [Leaflet Routing Machine (unmaintained)](https://www.github.com/perliedman/leaflet-routing-machine) · [Mapbox free tier](https://freetier.co/directory/products/mapbox)
