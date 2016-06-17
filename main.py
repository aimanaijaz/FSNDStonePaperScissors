#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import StonePaperScissorsApi

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to Users who have unfinished games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        for user in users:
            games = Game.query(Game.user == user.key).\
            filter(Game.game_over == False)
            if games.count() > 0:
                subject = 'This is a reminder!'
                body = 'Hello {}, you have games that are in progress!'.format(user.name)
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                               user.email,
                               subject,
                               body)


class UpdateUnfinishedGamesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update announcement in memcache."""
        StonePaperScissorsApi._cache_unfinished_games()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_unfinished_games', UpdateUnfinishedGamesRemaining),
], debug=True)
