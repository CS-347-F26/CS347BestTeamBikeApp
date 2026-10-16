# Final Project Plan - Idea 32, Bike Transit Map

## Idea from the Website
32. Bike Transit Map
Dr. Bowers wants to be able to create a map of a community (e.g. Harrisonburg) that encodes vetted/safe/efficient bike routes. Then a visitor to the app, planning their ride would tell the thing the begin and end, and the app would try to keep them on the vetted routes as much as possible.

Client (other than Dr. Stewart)
Dr. Bowers

(Just write your [Plan](https://w3.cs.jmu.edu/cs347/f26/project/plan/) right here in this README. You can edit this file however you like.)

## Sketch

Your **design sketch** must...

* **NOT DEPICT USER REGISTRATION, SIGN IN, NOR SIGNOUT**
* depict the main "screens" for an unauthenticated user (e.g. landing page, else?)
 * include possible url for each of these screens
* depict the main "screens" for an authenticated user
 * include possible url for each of these screens
* depict user interface elements necessary to perform CRUD operations.
* depict a navigation menu that will be present on all pages.

## Narrative

Your **project narrative** must begin with the project title, your team name, and the student names and include the following sections (about 200 words each):

* Purpose
 The main idea of our project is to create a bike transit map for the city of Harrisonburg, VA. This map will encode vetted safe efficient bike routes. Currently, if you use Google Maps, Apple Maps, or other navigational software for bike routes, the most efficient bike route may not be the safest. Common problems with vague maps of the area include: not knowing elevation changes, not knowing dangerous or construction areas, riding on the side walk instead of bike lanes, etc. This web app will benefit new people local to the community and provide better context for safer and more enjoyable bike trips.
 
* Users
 * Identify the primary users of your application, including their background or needs.
 * Justify how your application will benefit these users and improve their experience.
 The primary user of our adaptation will be locals, visitors, students, and professors who live in the Harrisonburg community. Locals and students both have separate needs for this app. For example, locals will most likely want to stay outside campus and avoid high traffic areas around campus, and are likely coming and going from their house or workplace. Students however, will most likely want to stay near campus and are commuting to/from class. Students will also frequent different places than locals like cheaper grocery stores, off campus book store, etc. This application will enable users to easily route their bike path that best aligns with their lifestyle.

* Features
 * Outline the core functionalities of your application and explain how they will work.
 * Provide a concrete example demonstrating how the application fulfills its purpose.

 - bike parking
 - authentication system
 - routes (they put in a location they want to go to)
 - efficient route vs safest route vs easiest route vs scenic route
 - filtering between different types of users (student, local, etc.)
 - Track favorite routes or favorite places
 - saved locations like home, 
 - users make route ratings on safety, comfort, intensity, traffic, etc.
 - at the end of the route, users will information that shows their route, the time it took, mileage, etc. Users can then export their data.
 - users can set way-points that users can place as to different locations they wanna avoid, prefer, etc. Way-points are shared between all users. Other users can then give the way-points thumbs up or thumbs down to "rate" the different way-points.
 - import/export you can send different routes to people
 - their might also be a previous routes section where users can see all the data of their previous routes. 

* Data
 * Describe the types of data that users will create, read, update, and delete (CRUD).
 * Include an example of this data using either real or representative sample values.
 * Include objects and their properties with some notion of those properties types
 * Include your intended relationships between your objects.

 Users will create, read, update and delete their route data, route ratings, saved/pinned locations, favorite locations. An example of this data is to have users have user id's that correspond to each of their individual data. 
 
 Way-points will also have their own data. This will look like the amount of likes and dislikes each way-point has, the latitude and longitude of the way-point, the comments people have on each way-point.
 
 For example, they can have an array of saved locations


## Claims
(Dorian's draft. Please review!)
Our claims will be:
 - Basic claims B10 - B121
 - I100: Application has in-app documentation
 - I60: Application has data import/export -- export a link to send to your friend to open in-app ala Spotify playlist?
 - I90: Application is mobile-responsive
 - I130: Application has data visualization (idk how smart this is of an idea but I love visualization!)
 - I170: Application has internationalization (considering we go to school in a multicultural city this is a good idea)
 - S80: Notifications (via Push)????? (construction, accident ahead, etc.)
 - S40 for crowdsourcing and maintenance.
 - Also a claim: Text-to-speech
Draft your expectation of which [claims](./claims.md) you will make for your project

References are optional, but you may include "Works Cited" if that simplifies the explanation.



## Stew Notes:
* Right now, if one were to map a bike ride in Google Maps, it just goes for the most efficient
* However, cycling veterans know where/where not to go, and this app lets them give recommendations
* Are we building this for Harrisonburg? Also, are you building the map yourself (please don't)
* Prefer suboptimal routes that build a sense of geography instead?
* Crowdsourcing ideas:
    * Bottleneck it on one person
        * Permission-based: a conclave of cyclist-routing gurus or something (Stretch Goal S40)
        * Problem with above is that it's bottleneck and requires vigilance on the stakeholder's part to keep it updated, etc.
        * Make org via Github?
* Why are we not just using Google Maps? Is there a way to store info in the database such that we could plug those into Google Maps and have it make the turn-by-turn for us? Could just be as simple as a generated link to Google Maps/Apple Maps/whatever
    * Is there a way to craft the route such that it's not like a million little destinations?
    * Hopefully we can make this on the free.


## Notes from Meeting w/ Bowers:
* **Original Idea**: Organize bike routes in a town and display it like a London tube/DC metro map
    * i.e. ride on green route, then turn on read
    * Needs to be crowdsourced somehow, and someone needs to makedecisions
    * Data can inform city planners so they can provide infrastructure around popular routes (bike lanes, signage, etc.)
* Since it looks like DC Metro Map, we need to take Harrisonburg and abstract it
* Provide alternatives; safer routes vs faster routes and all that
* **How to crowdsource a path?**
    * Just try drawing a route? Annotate too (i.e. this section is gravel)
    * Interview avid cyclists and see what routes they take?
    * Allow users to plot their own routes/waypoints?
    * **Considerations when cycling:** Quality of road, mean dog present, traffic density, etc.
        * Can report hazards when driving?
        * Dashed lines instead of solid
* **Reason behind app:** More people will likely ride bikes if they're more aware of safe routes
    * Cyclist-approved map of where to go
    * Transit system-style app
    * If successful or useful, make it in such a way that it can be implemented for multiple cities
    * Harrisonburg already has a solution. It's too much info. **Beat that.**
* **Navigation:**
    * Navigation along the abstracted map. Less "make a left turn in 300 yards," more "intersection for Red Route coming up."
    * Filter routes by comfort score?
    * Also include navigation for when you're on the route
    * Allow folks to report routes if they're dangerous, etc.