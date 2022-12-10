TODO

*        Error handling on new user registration
* [DONE] Alter Volunteer relation to use Django 'through'
*        User details page (auth rqd.)
*        User edit page (auth rqd.)
*        User cancellation page (auth rqd.)
         *        Need to cancel any events first
         *        Need to cancel any volunteering first
*        User dashboard (my events and my volounteering)  (auth rqd.) (use new component, see below)
* [DONE] New Event page (auth rqd.)
* [DONE] Event listing page
         *        Add navigation for all/past
         * [DONE] Filter volunteer links on event cancelled and user already volunteered
* [DONE] Event detail page
         * [DONE] Filter volunteer links on event cancelled and user already volunteered
* [DONE] Event cancellation page
*        Volunteer for event page (auth rqd.)
         *        Can't volunteer if
                  *        Event in the past
                  *        Event cancelled
                  *        User already volunteered
* Cancel volunteering (auth rqd.)
         *        Can't cancel if
                  *        User not already volunteered
                  *        Event cancelled
                  *        Event in the past
* Abstract out event listing componenet
* Rework event listing to use new component
* Add 'upcomming events with not enough helpers' to index page
* Review url structure (esp event/events)
