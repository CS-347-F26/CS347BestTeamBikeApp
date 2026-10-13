# Claims

**NOTE: this file will likely diverge from [the official version](https://w3.cs.jmu.edu/cs347/f26/project/implementation/). i will try not to change any claims' identifiers (i.e. B10 should remain B10, and its semantics should also remain fixed)

Teams will build a useful backend web application in Django with a functional and attractive frontend. To earn points, teams make "claims" - concrete accomplishments toward their application. All teams must deploy their application to a hosting service to receive a grade.

## Grading Scheme

Each claim is worth a certain number of points. The grading scale is as follows:

| Points    | Letter Grade |
| --------- | ------------ |
| 900-1000  | A            |
| 800-899   | B            |
| 700-799   | C            |
| 600-699   | D            |
| Below 600 | F            |

In addition, the following requirements must be met for a letter grade:

- Application must be deployed and accessible via URL to receive a D or higher.
- A deployed application with only partial Basic Claims implemented will receive a D (650).
- Application must implement all Basic Claims to receive a C or higher (700).
- Application must implement all Basic and eight Intermediate Claims to receive a B or higher (800).
- Application must implement all Basic, eight Intermediate, and one Stretch Claim to receive an A (900).

Each extra Intermediate Claim beyond the required eight adds 10 points. A second Stretch claim adds 50 points. No more that two Stretch claims can be counted. A team's score is capped at 1000 points.

## Four+-Person Teams

Teams of four (or more) students face slightly higher requirements:

- Application must be deployed and accessible via URL to receive a D or higher.
- A deployed application with only partial Basic Claims implemented will receive a D (650).
- Application must implement all Basic Claims to receive a C or higher (700).
- Application must implement all Basic and ten Intermediate Claims to receive a B or higher (800).
- Application must implement all Basic, ten Intermediate, and two Stretch Claims to receive an A (900).

Each extra Intermediate Claim beyond the required ten adds 10 points. A third Stretch claim adds 50 points. No more that three Stretch claims can be counted. A team's score is capped at 1000 points.

## When to Make Claims

A claim should be made when the feature is fully implemented and tested. Claims can be made at any time during the project, but it is recommended to make claims as soon as possible to ensure they are evaluated before the project deadline.

Claims may generally be made at two times:

1. **During a lab or work session**: Ask the instructor to evaluate your claim. He will check the feature and, if it meets the requirements, mark it as completed and award points.
2. **In office hours**: If you are unable to make a claim during a lab or work session, you can visit the instructor during office hours to have your claim evaluated.

Note: **No more than three non-Basic claims can be made in a week.** Plan accordingly. Claims cannot be made once final exam week begins.

---

Claims marked with an asterisk (*) indicate that the claim should be evaluated at the end of the project, not during development.

## Basic Claims

### Core Application Structure

- **B10: Application has a front page** - Landing page that loads successfully  
  *Assessment: Homepage URL loads without errors and displays content*
- **B20: Application has navigation** - Menu or navigation system linking multiple pages  
  *Assessment: Navigation menu visible on multiple pages with working links*
- **B30: Application uses Django admin interface** - Admin panel accessible and functional for all models  
  *Assessment: /admin/ URL accessible, can log in, all models visible and manageable*
- **B40: Application has 3 distinct models** - At least three different Django models with appropriate fields, other than User  
  *Assessment: Three custom models defined in models.py with meaningful fields*
- **B50: Models are stored in database** - Data persists between sessions using Django ORM  
  *Assessment: Data added through app persists after server restart*
- ***B60: Application handles 404 errors gracefully** - Custom 404 page or appropriate error handling  
  *Assessment: Invalid URLs show custom 404 page or appropriate error message*
- ***B70: Models have meaningful relationships** - Foreign keys, many-to-many, or one-to-one relationships implemented  
  *Assessment: At least one relationship defined between models and functioning*
- ***B80: Application has proper URL routing** - Clean, meaningful URLs using Django's URL patterns  
  *Assessment: URLs are readable and follow RESTful conventions*

### User Interface & Templates

- **B90: Application uses Django templates** - HTML rendered using Django's template system  
  *Assessment: Pages use .html templates in templates/ directory with Django template syntax*
- **B100: Templates use template inheritance** - Base template with child templates extending it  
  *Assessment: Base template exists and at least 2 templates extend it using {% extends %}*
- ***B110: Application has consistent styling** - CSS applied across multiple pages with cohesive design  
  *Assessment: CSS file linked and consistent styling visible across 3+ pages*
- ***B120: Forms are styled and user-friendly** - Form inputs have labels, styling, and clear layout  
  *Assessment: Forms have proper labels, styling, and submit buttons*
- ***B121: Application meets automated a11y checks** - Passes [WAVE](https://wave.webaim.org/)
  *Assessment: Forms have proper labels, styling, and submit buttons*
  

### CRUD Operations

*Note: CRUD operations do not need to be implemented for all models, but at least one model must have full CRUD functionality. Make your interfaces as natural as possible -- not just forms and tables, for instance.*

- **B130: Create functionality works** - Users can add new records through the web interface  
  *Assessment: Can create new records via web form, data appears in database*
- **B140: Read functionality works** - Users can view lists and details of records  
  *Assessment: Can view list of records and individual record details*
- **B150: Update functionality works** - Users can edit existing records through the web interface  
  *Assessment: Can edit existing records via web form, changes persist*
- **B160: Delete functionality works** - Users can remove records through the web interface  
  *Assessment: Can delete records via web interface, records removed from database*

### Authentication & Security

- **B170: Application has user login/logout** - Users can sign in and out of the system  
  *Assessment: Login/logout forms work, user session maintained*
- **B180: Application enforces authentication** - Some pages require login to access  
  *Assessment: At least one page redirects to login when accessed anonymously*
- ***B190: Application has basic security measures** - CSRF protection and secure forms  
  *Assessment: Forms include {% csrf_token %} and CSRF middleware enabled*

---

## Intermediate Claims

### Advanced Features

- **I10: Application handles file uploads** - Users can upload and store files (images, documents, etc.)  
  *Assessment: File upload form works, files stored and retrievable*
- **I20: Application has search functionality** - Users can search and filter content  
  *Assessment: Search form returns relevant results, filters work*
- **I30: Application has user profiles** - Users can view and edit their profile information  
  *Assessment: User profile page exists and is editable*
- **I40: Application has pagination** - Large lists are broken into pages for better UX  
  *Assessment: Lists with 10+ items show pagination controls*

### Data & Relationships

- **I50: Application validates user input** - Form validation with appropriate error messages  
  *Assessment: Forms show error messages for invalid input*
- **I60: Application has data import/export** - Ability to import data from files or export data  
  *Assessment: Can import/export data via CSV, JSON, or similar format*

### API Integration

- **I70: Application integrates external API** - Uses at least one third-party API (weather, maps, social media, etc.)  
  *Assessment: External API data displayed and functional in app*
- **I80: Application provides its own API** - RESTful endpoints that return JSON data  
  - *Assessment: API endpoints return valid JSON and respond to requests*
  - *Assessment: API endpoints require appropriate authentication*

### Polish & Usability

- **I89: Application passes manual a11y testing** - Tested via [Accessibility Insights for Web](https://microsoftedge.microsoft.com/addons/detail/accessibility-insights-fo/ghbhpcookfemncgoinjblecnilppimih)
  *Assessment: repo includes a document detailing the manual testing completed, efforts/commits/changes required to resolve issues, and results of final testing*
- ***I90: Application is mobile-responsive** - Works well on mobile devices and tablets  
  *Assessment: App layout adapts to mobile screen sizes (test at 375px width)*
- **I100: Application has in-app documentation** - Help pages, tooltips, or user guides within the app  
  *Assessment: Help content accessible within app interface*
- **I110: Application has advanced forms** - Multi-step forms, dynamic forms, or complex form widgets  
  *Assessment: Forms use advanced widgets or multi-step functionality*
- **I120: Application has custom middleware** - Custom Django middleware for logging, authentication, or other functionality  
  *Assessment: Custom middleware class defined and functioning*
- **I130: Application has data visualization** - Charts, graphs, or other visual data representations  
  *Assessment: Data displayed in charts/graphs using libraries like Chart.js*
- **I140: Application implements permissions system** - Fine-grained permissions beyond basic authentication  
  *Assessment: Different user types have different access levels*
- **I150: Application has bulk operations** - Users can perform actions on multiple records at once  
  *Assessment: Can select and act on multiple items simultaneously*
- **I160: Application has audit trail** - Track changes to important data with timestamps and user info  
  *Assessment: Changes logged with user and timestamp information*
- ***I170: Application has internationalization** - Support for multiple languages or locales  
  *Assessment: App displays in at least 2 languages using Django i18n*
- ***I180: Application has comprehensive logging** - Detailed logging system for debugging and monitoring  
  *Assessment: Application events logged to files or console*

---

## Stretch Claims

### Advanced Architecture

- ***S10: Application uses a frontend framework** - Frontend framework (React, Vue, Angular) with Django REST backend  
  *Assessment: Frontend framework implemented with Django REST API backend*
- **S20: Application is a Single Page Application (SPA)** - Dynamic frontend with client-side routing  
  *Assessment: SPA functionality with client-side routing and dynamic content loading*
- **S30: Application uses WebSockets** - Real-time features like chat, live updates, or notifications  
  *Assessment: Real-time functionality working with WebSocket connections*

### Complex Features

- **S40: Application has advanced user roles** - Multiple user types with different permissions and capabilities  
  *Assessment: 3+ distinct user roles with different interface/functionality*
- **S50: Application has real-time communication** - Multiple users can meaningfully communicate with each other via the app (audio and or video)  
  *Assessment: Multiple users can join a "call" via [WebRTC](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)*
- **S60: Application has real-time collaboration** - Multiple users can work on the same content simultaneously  
  *Assessment: Multiple users can edit same content with live updates*
- **S70: Application canvas Canvas API** - makes meaningful use of (Instructure's) Canvas API
  *Assessment: External API data displayed and functional in app*
- **S80: Notifications (via Push)** - uses [push notifications](https://developer.mozilla.org/en-US/docs/Web/API/Push_API) meaningfully
  *Assessment: Push permissions are requested and meaningful push notification is sent/received successfully*

### Innovation & Polish

- **S89: Application implements a11y in CI** - Automated a11y testing is implemented as a part of a Continuous Integration pipeline.
  *Assessment: repo includes a document the CI and links to example runs/results*
- **S90: Application has unique or innovative features** - Creative functionality not included here  
  *Assessment: Feature approved by instructor and successfully implemented*
 	- *Note: Propose your own unique feature for approval BEFORE you start working on it*
- **S100: Application has machine learning integration** - Uses ML models for recommendations, predictions, or classification  
  *Assessment: ML model integrated and providing useful predictions/recommendations*
- **S110: Application has LLM integration** - Uses large language models (e.g., GPT) for advanced text generation, summarization, or conversation  
  *Assessment: LLM API integrated and providing text generation functionality*
 	- *Note: You will need to find a free tier or educational access to an LLM API*
- **S120: WebAssembly** - Frontend written in a language other than js and deployed via webassembly
  *Assessment: ...*
- **S130: 3D** - Frontend uses Three.js or other to have an immersive 3D User Interface
  *Assessment: ...*
