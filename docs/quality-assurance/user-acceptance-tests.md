## Old user tests

### Test1
Given
- the registration page (no prerequisites)
When the user inputs
- their name & surname
- an email of a valid format
- a password
Then the app should
- create a new profile with specified properties
- log the user in

### Test2
Given
- a logged in profile
When the user
- creates a game
- specifies custom settings of the game
- starts the game
then the app should
- perform the game according to specified settings

### Test3
Given
- a completed game
When the user
- clicks “save deck” button
- inputs a deck name
- inputs a set of tags
Then 
- the deck is added to their profile
- the deck is available for future games from that point 

## New user tests

### Test4
Given
- a logged in user
- a saved deck in user's profile
When the user
- clicks 'edit'
- changes deck attributes (deck name or words in the deck)
- clicks 'save'
Then
- the changes are saved in the database
- on the next deck view/use, the changes are applied

### Test5
Given
- a set (3+) of logged in users
When
- one of the users hosts a game with more than 1 team
- other users join different teams
Then
- game is processed for each team separately
