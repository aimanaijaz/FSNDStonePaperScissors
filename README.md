#Full Stack Nanodegree Project Design a game

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
  
##Game Description:
Stone Paper Scissors is a simple game between 2 players. Each game has a fixed number of rounds (default 5).      
In each round you choose to play either stone, paper or scissors. The 2nd player which is AI here plays stone, paper or scissors as well.      
The rules of the game are:      
1. Paper beats Stone   
2. Scissors beats Paper   
3. Stone beats Scissors    
You score a point for each round you win.   
If you both(you and AI) choose the same move for example both choose paper, the round is a tie and we repeat that round.   
When all the rounds(default 5) have been played, you are declared the winner if you win more than half of the rounds that you played.      
Otherwise you lose the game

Many different Stone Paper Scissors games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, rounds
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Also adds a task to a task queue to update the unfinished games   

 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, play
    - Returns: GameForm with new game state.
    - Description: Accepts a 'play' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_unfinished_games**
    - Path: 'games/unfinished_games'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the number of unfinished games.


##Additional endpoints:

 - **get_high_scores**
    - Path: 'highscore'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Gets the scores in descending order.

 - **get_user_ranking**
    - Path: 'user/userrankings'
    - Method: GET
    - Parameters: None
    - Returns: UserRankingForms
    - Description: Gets user ranking based on win rattios.

 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/gamehistory'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: Gets the history of all moves for a particular game.

 - **get_user_games**
    - Path: 'user/usergames'
    - Method: GET
    - Parameters: user_name, email (optional)
    - Returns: GameForms
    - Description: Gets all the active games for a particular user.

 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancelgame'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: Message confirming deletion of game
    - Description: Deletes unfinished games.


##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **GameForms**
    - Multiple GameForm container
 - **NewGameForm**
    - Used to create a new game (user_name, rounds)
 - **MakeMoveForm**
    - Inbound make move form (play).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    game_score).
 - **ScoreForms**
    - Multiple ScoreForm container.
- **UserRankingForm**
    - Representation of a user with ranking information (name, wins, total_played,
    win_ratio).
 - **UserRankingForms**
    - Multiple UserRankingForm container.
 - **StringMessage**
    - General purpose String container.