TODO

* Error handling on new user registration
* [DONE] Alter Volunteer relation to use Django 'through'
* User details page (auth rqd.)
* User edit page (auth rqd.)
* User cancellation page (auth rqd.)
         * Need to cancel any events first
         * Need to cancel any volunteering first
* User dashboard (my events and my volunteering)  (auth rqd.) (use new component, see below)
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
* Don't show 'Volunteer' link in tables if already volunteered
* Require authentication, put login/register on index page
* [DONE] Add a UniqueConstraint on user/event in Volunteers
* Add transaction protection to update views
* User cancellation and user suspension
* Rework 'user has volunteered' or 'user owns event' tests to use equality
* [DONE] Rename 'set' relations in Event
