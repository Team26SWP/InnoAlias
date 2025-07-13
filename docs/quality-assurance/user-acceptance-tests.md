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

Issues:
https://github.com/Team26SWP/InnoAlias/issues/19
https://github.com/Team26SWP/InnoAlias/issues/29
https://github.com/Team26SWP/InnoAlias/issues/31

### Test2
Given
- a logged in profile

When the user
- creates a game
- specifies custom settings of the game
- starts the game

then the app should
- perform the game according to specified settings

Issues:
https://github.com/Team26SWP/InnoAlias/issues/25
https://github.com/Team26SWP/InnoAlias/issues/24

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

Issues:
https://github.com/Team26SWP/InnoAlias/issues/73
https://github.com/Team26SWP/InnoAlias/issues/70
https://github.com/Team26SWP/InnoAlias/issues/69
https://github.com/Team26SWP/InnoAlias/issues/68

### Test4: deck editing
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

Issues:
https://github.com/Team26SWP/InnoAlias/issues/133
https://github.com/Team26SWP/InnoAlias/issues/130
https://github.com/Team26SWP/InnoAlias/issues/131
https://github.com/Team26SWP/InnoAlias/issues/132

### Test5: teams game mode
Given
- a set (3+) of logged in users

When
- one of the users hosts a game with more than 1 team
- other users join different teams

Then
- game is processed for each team separately

Issues:
https://github.com/Team26SWP/InnoAlias/issues/65
https://github.com/Team26SWP/InnoAlias/issues/66
https://github.com/Team26SWP/InnoAlias/issues/67

### Test6: deck gallery
Given 
- a logged in user
- a completed game

When
- the user pick "public" on deck saving

Then
- the deck is added into the gallery in the database
- the deck is now available to all users

Issues:
https://github.com/Team26SWP/InnoAlias/issues/164
