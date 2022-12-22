# TODO

* [DONE] Alter Volunteer relation to use Django 'through'
* [DONE] User dashboard (my events and my volunteering)  (auth rqd.) (use new component, see below)
* [DONE] New Event page (auth rqd.)
* [DONE] Event listing page
         * [DONE] Add navigation for all/past
         * [DONE] Filter volunteer links on event cancelled and user already volunteered
* [DONE] Event detail page
         * [DONE] Filter volunteer links on event cancelled and user already volunteered
* [DONE] Event cancellation page
* [DONE] Volunteer for event page (auth rqd.)
* [DONE] Cancel volunteering (auth rqd.)
* [DONE] Abstract out event listing component
* [DONE] Rework event listing to use new component
* [DONE] Add 'upcomming events with not enough helpers' to index page
* [DONE] Review url structure (esp event/events)
* [DONE] Rework event listing with toggle button future/all, drop upcoming needing volunteers
* [DONE] Don't show 'Volunteer' link in tables if already volunteered
* [DONE] Add a UniqueConstraint on user/event in Volunteers
* [DONE] Rework 'user has volunteered' or 'user owns event' tests to use object equality
* [DONE] Rename 'set' relations in Event
* [DONE] In Event create, split start into date and time, and duration i H and M
* [DONE] Add transaction protection to update views
* [DONE] Require authentication, put login/register on index page
* [DONE] Validate start when creating events
* [DONE] Improve Admin display of objects
* [DONE] Error handling on new user registration
* [DONE] User details page (auth rqd.)
* [DONE] User edit page (auth rqd.)
* [DONE] User cancellation page (auth rqd.)
         * [DONE] Need to cancel any events first
         * [DONE] Need to cancel any volunteering first
* [DONE] Honour user cancellation and user suspension
* [NOT DOING] Support for un-cancelling
* [DONE] Privacy policy

* Better descriptive text on Index page
* Re-style all pages


