## Functional stability

### Functional Correctness
Ensuring game rules are enforced accurately is paramount. Players expect consistent word validation and scoring to maintain competitive integrity. Incorrect behavior would ruin gameplay and cause player to leave the game.

#### Test: Word Validation Accuracy
**Quality Attribute Scenario**:
- **Source**: Player submits guess
- **Stimulus**: Enter word into input field and get a point
- **Artifact**: Validation logic on backend
- **Environment**: Active game round
- **Response**: Correctly accepts valid words/rejects invalid ones
- **Response Measure**: 100% accuracy with 1000 test words

**Execution Method**:
1. Create test .txt file with 1000 words
2. Manually entering the correct/incorrect words
3. Verifying that scoring increments properly


### Functional Appropriateness
Our customer prioritizes lean, intentional design where all functionalities directly contribute to the word-guessing challenge. 

#### Test: Input Field Behavior Validation
**Quality Attribute Scenario**:

- **Source**: Player during timed round
- **Stimulus**: Type guess into input field
- **Artifact**: Input handling system
- **Environment**: Active game with 30s timer
- **Response**: Field optimizes for rapid word entry without distractions
- **Response Measure**: 95% of players clearly understand the main goal of app. 


**Execution Method**:
1. Find 15 new users among students
2. Ask them to go through couple of games
3. Conduct a survey among these users about UI decisions made 




## Interaction capability

### Self-descriptiveness
Intuitive interfaces minimize learning curves. Clear input guidance and error feedback prevent player frustration during timed rounds.

#### Test: New user UI usage
**Quality Attribute Scenario**:
- **Source**: New player
- **Stimulus**: Create a game
- **Artifact**: UI create game button
- **Environment**: Home page
- **Response**: Correctly creates a game with settings that new players wants
- **Response Measure**: 100% of users intuitively understand the UI.

**Execution Method**:
1. Find 15 new users among students
2. Ask them to go through couple of games
3. Conduct a small survey about UI among new users



