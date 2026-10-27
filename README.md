# Final Project Plan - Idea 32, Bike Transit Map

## Idea from the Website
32. Bike Transit Map
Dr. Bowers wants to be able to create a map of a community (e.g. Harrisonburg) that encodes vetted/safe/efficient bike routes. Then a visitor to the app, planning their ride would tell the thing the begin and end, and the app would try to keep them on the vetted routes as much as possible.

Client (other than Dr. Stewart)
Dr. Bowers

(Just write your [Plan](https://w3.cs.jmu.edu/cs347/f26/project/plan/) right here in this README. You can edit this file however you like.)

## Sketch
Desktop View: ![Desktop View](/images/Desktop.png.png)
Mobile View: ![Mobile View](/images/Mobile.png)

## Narrative

Your **project narrative** must begin with the project title, your team name, and the student names and include the following sections (about 200 words each):

* Purpose
The main idea of our project is to create a bike transit map that is abstracted like a subway map.  This map will encode vetted, safe, efficient bike routes.  Currently, if you use Google Maps, Apple Maps, etc. for bike routes, the most efficient bike route may not be the safest.  This web app will benefit new people in the community and provide better context for more enjoyable, safer bike trips.  Common problems with bike maps include information overload or ignoring unsafe areas, routes with high elevation, etc.  Other bike maps also don't factor in shortcuts or other user tips.  While there is a bike map produced by Harrisonburg Department of Public Transportation (HDPT), it provides too much information and has no nuance.  If this app grows in popularity, it could motivate more people to use bicycles, and we could gather data to provide HDPT for future reference.
 
* Users
The primary users of our application will be locals, visitors, students, and professors who live in the Harrisonburg community.  Locals and students both have separate needs for this app.  For example, locals will most likely want to stay within town lines and avoid high-traffic areas around campus.  They will likely be coming and going from their home or workplace.  Students, however, will most likely want to stay near campus and are coming and going from class.  Students will also frequent different places than locals.  This application will improve these users' experience by letting them easily route their bike path to best match their lifestyle.

* Features
- These bike routes will be differentiated by different colors
- Ex: ![DC Metro Map](/images/DCMetro.png)
- Users can select routes and receive directions as they travel. While riding, the app shows turn-by-turn directions along the vetted routes (e.g. ‘In 300 ft, turn left onto Main St’), plus route-level cues for transfers and arrival.
- Users will be able to give their opinion on different bike routes.  For example, if a cyclist felt unsafe on the green route, they can add comments or mark said area. All users will be able to see these comments/marks.
- Examples of things users can mark include high-traffic areas, gravel paths, mean dogs, etc.
- Version 2 - While users are on their route, the app will speak directions so they know where to go next.  The app will also tell users when they can switch routes mid-ride.
- Different line types on the bike map can indicate a route's safety. For example, a dashed line might indicate rough terrain.
- The app can suggest different routes based on the user’s comfort level by using a comfort score.
- Navigation. Riders choose a start and end station on our network, and the app computes a path over our vetted-route graph using our own implementation of Dijkstra's algorithm. While riding, the app gives turn-by-turn directions along the vetted routes (e.g. "In 300 ft, turn left onto Main St") plus cues for transfers and arrival, based on the rider's GPS position. Turn instructions are generated once with openrouteservice when we build each route and stored in our database, so no outside navigation service is used during rides. Version 2 reads directions aloud using the browser's built-in Web Speech API. We will not give directions to the first station (riders get there on their own, like walking to a subway stop) or reroute riders who leave the network. The route network is curated by our team with Dr. Bowers, using the City of Harrisonburg's Community Bike Map as a starting point.


* Data
See our data model here: ![Data model](/images/DataModel.jpeg)
Users will be able to do CRUD operations on any data within the user entity with the exception of ID.  So they can create, read, update and delete their own username, password, previous routes, saved routes, marked locations, and comfortability.  Users will also be able to do CRUD operations on their own comments.

An example of this data using the user entity:
- ID: 1234
- Username: biker_24
- Password: I_lov3-bIkIng43
- Prev_routes: route_id: 23, route_id, 45, route_id: 32
- Saved_routes: route_id: 52, route_id, 1, route_id: 35
- marked_locations : Location_id: 234, location_id: 39
- Comfortability: 2
- Comments: comment_id: 23, comment_id: 64



## Claims
Our claims will be:
Basic claims B10 - B121
- I89: Application passes manual a11y testing(?)
- I100: Application has in-app documentation
- I60: Application has data import/export -- export a link to send to your friend to open in-app ala Spotify playlist?
- I90: Application is mobile-responsive
- I160: Application has audit trail (helpful for timestamps & route changes)
- I180: Application has comprehensive logging
- I20: Application has search functionality
- I30: Application has user profiles (comfortability, etc.)
- I130: Application has data visualization (idk how smart this is of an idea but I love visualization!)
- I170: Application has internationalization (considering we go to school in a multicultural city this is a good idea)
- S80: Notifications (via Push)????? (construction, accident ahead, etc.)
- S40 for crowdsourcing and maintenance.
- Also a claim: Text-to-speech


References are optional, but you may include "Works Cited" if that simplifies the explanation.