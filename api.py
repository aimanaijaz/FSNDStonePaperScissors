#import statements
import random
import logging
import endpoints
# Used for sorting
from operator import itemgetter, attrgetter, methodcaller
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, GameForms, MakeMoveForm, ScoreForms, UserRankingForm, UserRankingForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)

USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
VALID_MOVES = ['stone', 'paper', 'scissors']

MEMCACHE_UNFINISHED_GAMES = 'UNFINISHED_GAMES'

@endpoints.api(name='stone_paper_scissors', version='v1')
class StonePaperScissorsApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        game = Game.new_game(user.key,request.rounds)

        taskqueue.add(url='/tasks/cache_unfinished_games')
        return game.to_form('Good luck playing Stone Paper Scissors!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Here is some game info!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if not game:
            raise endpoints.NotFoundException('Game not found!')
        if game.game_over:
            game.ai_move = ""
            return game.to_form('Game already over!')
        # Make sure that AI move is valid
        game.ai_move=random.choice(VALID_MOVES)
        # Decrement the number of rounds remaining
        game.rounds_remaining -= 1
        # Allowing user input to be case insensitive
        request.play = request.play.lower()
        # Make sure that User play is valid
        if not request.play in VALID_MOVES:
          raise endpoints.BadRequestException("Invalid Move")
        # Check conditions to win the round. If user wins the round increments his points and append move to game history
        if ((request.play == "paper" and game.ai_move == "stone") or 
            (request.play == "stone" and game.ai_move == "scissors") or
            (request.play == "scissors" and game.ai_move == "paper"))  :
            msg = '{} beats {} . You win this round!'.format(request.play, game.ai_move)
            game.points += 1
            game.history.append(("You Played: {}".format(request.play), "AI Played: {}".format(game.ai_move), "You Won"))
        # Check if there is a tie. If there is a tie ask the user to play this round again and append move to game history
        elif((request.play == "paper" and game.ai_move == "paper") or 
            (request.play == "stone" and game.ai_move == "stone") or
            (request.play == "scissors" and game.ai_move == "scissors")):
            game.rounds_remaining += 1
            msg = 'Its a tie. Play again'
            game.history.append(("You Played: {}".format(request.play), "AI Played: {}".format(game.ai_move), "Its a Tie"))
        # If above conditions are not met the user loses the round. Append this move to game history
        else:
            msg = '{} beats {}. You lost this round.'.format(game.ai_move, request.play)
            game.history.append(("You Played: {}".format(request.play), "AI Played: {}".format(game.ai_move), "You Lost"))

        if game.rounds_remaining < 1:
            # User wins the game if he/she wins more than half the rounds. For example if there are 10 rounds user should win more than 5 rounds to win the game
            if (game.points>(game.rounds_allowed/2)):
              game.end_game(True)
              result = 'Congratulations!! You scored enough points. You won!!'
            else:  
              game.end_game(False)
              result = 'Sorry!! You did not score enough points. You lost!!'
            return game.to_form(msg +' Game over!' +result)
        else:
            game.put()
            return game.to_form(msg)


    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=ScoreForms,
                      path='highscore',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Return scores in descending order"""
        Scores =Score.query(Score.won == True).order(-Score.game_score)
        return ScoreForms(items=[score.to_form() for score in Scores])

    @endpoints.method(response_message=UserRankingForms,
                      path='user/userrankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Returns user's user_rankings based on win ratios"""
        allusers =User.query(User.total_played > 0).fetch()
        # Sorting using attrgetter. Reference https://wiki.python.org/moin/HowTo/Sorting
        allusers = sorted(allusers, key=attrgetter('win_ratio'), reverse=True)
        return UserRankingForms(items=[user.to_form() for user in allusers])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/gamehistory',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Returns a history of all moves for a game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
          raise endpoints.NotFoundException('Game not found!')
        return StringMessage(message=str(game.history))

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='user/usergames',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
          raise endpoints.NotFoundException('A user with that name does not exist!')
        games = Game.query(Game.user == user.key)\
                .filter(Game.game_over == False)
        return GameForms(items=[game.to_form("Active game") for game in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/cancelgame',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Deletes unfinished games."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                raise endpoints.ConflictException('Game already over. Completed games cannot be deleted!')
            else:
                game.key.delete()
                return StringMessage(message='Game {} cancelled!'.format(request.urlsafe_game_key))
        else:
              raise endpoints.NotFoundException('Game does not Exist!')

    @endpoints.method(response_message=StringMessage,
                      path='games/unfinished_games',
                      name='get_unfinished_games',
                      http_method='GET')
    def get_unfinished_games(self, request):
        """Get the cached unfinished games"""
        return StringMessage(message=memcache.get(MEMCACHE_UNFINISHED_GAMES) or '')

    @staticmethod
    def _cache_unfinished_games():
        """Populates memcache with the number of unfinished games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            memcache.set(MEMCACHE_UNFINISHED_GAMES,
                         'The total unfinished games remaining is {}'.format(count))
     

api = endpoints.api_server([StonePaperScissorsApi])
