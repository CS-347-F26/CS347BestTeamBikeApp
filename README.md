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
  The main idea of our project is to create a bike transit map. This map will encode vetted safe efficient bike routes.  Currently, if you use google maps, apple maps, etc. for bike routes, the most efficient bike route may not be the safest.  This web app will benefit new people local to the community and provide better context for more enjoyable and safe bike trips.  This is important because of common problems with vague maps of the area like: not knowing elevation changes, not knowing dangerous or construction areas, bike lanes vs side walk, etc.
  
* Users
  * Identify the primary users of your application, including their background or needs.
  * Justify how your application will benefit these users and improve their experience.
  The primary user of our adaptation will be locals, visitors, students, and professors who live in the harrisonburg community.  Locals and students both have separate needs for this app.  For example, locals will most likely want to stay within town lines and avoid high traffic areas around campus.  They are likely coming and going from their house or workplace.  Students however, will most likely want to stay near campus and are coming and going from class.  Students will also frequent different places than locals like cheaper grocery stores, off campus book store, etc.  This application will improve these users' experiences because they will be able to easily route their bike path that best aligns with their lifestyle.

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
  - at the end of the route, users will information that shows their route, the time it took, mileage, etc.  Users can then export their data.
  - users can set way-points that users can place as to different locations they wanna avoid, prefer, etc.  Way-points are shared between all users.  Other users can then give the way-points thumbs up or thumbs down to "rate" the different way-points.
  - import/export you can send different routes to people
  - their might also be a previous routes section where users can see all the data of their previous routes. 

* Data
  * Describe the types of data that users will create, read, update, and delete (CRUD).
  * Include an example of this data using either real or representative sample values.
  * Include objects and their properties with some notion of those properties types
  * Include your intended relationships between your objects.

  Users will create, read, update and delete their route data, route ratings, saved/pinned locations, favorite locations. An example of this data, is to have users have user id's that correspond to each of their individual data. 
  
  Way-points will also have their own data. This will look like the amount of likes and dislikes each way-point has, the lattitude and longitude of the way-point, the comments people have on each way-point.  
  
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
 - S80: Notifications (via Push)?????
Draft your expectation of which [claims](./claims.md) you will make for your project

References are optional, but you may include "Works Cited" if that simplifies the explanation.



## Stew Notes:
* Right now, if one were to map a bike ride in Google Maps, it just goes for the most efficient
* However, cycling veterans know where/where not to go, and this app lets them give recommendations
* Are we building this for Harrisonburg? Also, are you building the map yourself (please don't)
* Prefer suboptimal routes that build a sense of geography instead?
