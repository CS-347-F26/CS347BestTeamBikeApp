

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