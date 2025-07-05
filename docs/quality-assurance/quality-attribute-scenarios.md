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
2. Manually entering the correct/incorrect 
