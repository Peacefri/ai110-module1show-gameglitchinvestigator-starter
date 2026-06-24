# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|---------------------|-----------------|------------------------|
|        | 
| | | | |
| | | | |
input : Click a button for New Game Reset
Expected Behavior:Clicking "New Game" or restarting should completely reset the game state
Actual Behavior: After completing a game, attempting to start a new game does not work
Console Output: None

input: ckecking on show hint feature does nothing
Expected Behavior: Toggling the "Show Hint" checkbox should display a relevant hint or dynamic guide to help the player
Actual Behavior: The "Show Hint" checkbox is completely non-functional. Checking or unchecking it reveals absolutely no hints, context, or visual feedback
Console Output: None

input: Select a difficulty level (Easy, Normal, or Hard) from the settings menu
Expected Behavior: Selecting a difficulty should instantly and accurately update both the guess number range and the allowed attempts across both the UI and the game logic:

Easy: range 1 to 20, attempts 6
Normal: range 1 to 100, attempts 8
Hard: range 1 to 50, attempts 5

Actual Behavior: The settings menu displays default ranges and attempt limits for each difficulty mode, but selecting a level causes UI and logic synchronization bugs:

Selecting a difficulty only updates the attempt count on the UI side — the actual guess number range does not update to match the selected level. All difficulties incorrectly show range 1 to 100 on the main game screen.
The actual number of attempts during gameplay does not match what is displayed in the settings menu:

Easy: settings shows 6 attempts, game shows 5
Normal: settings shows 8 attempts, game shows 7
Hard: settings shows 5 attempts, game shows 4
Console Output: None

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)? Gemini and Claude

I used Gemini and Claude as debugging teammates. A **correct** suggestion came when "New Game" wasn't resetting the game. The AI pointed out that I was only resetting `attempts` and `secret` but never set `status` back to `"playing"`, so the leftover `"won"`/`"lost"` status kept calling `st.stop()` and the new game never started. I verified this by clicking "New Game" after finishing a round and confirming the board reset, and the AI also noted the guess text box is a keyed widget that holds its old value, so I had to delete its session key too — which I confirmed by watching the input clear on the next run.

An **incorrect/misleading** suggestion was when the AI tied the "go HIGHER / go LOWER" feedback to the "Show hint" checkbox. Its fix put the directional message inside the hint logic, which created a new bug: when I entered another guess with the hint box unchecked, there was no "go higher" or "go lower" message at all, so the player had no way to know which direction to guess. I caught this by submitting several guesses with the hint off and seeing only a blank result with no guidance. I fixed it by always showing the directional message after a submit and letting the checkbox control only the extra standalone hint, then verified by guessing with the hint both on and off and confirming the higher/lower feedback always appeared.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
