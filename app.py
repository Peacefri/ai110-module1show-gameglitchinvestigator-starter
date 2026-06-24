import random
import streamlit as st

def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    if guess == secret:
        return "Win", "🎉 Correct!"

    try:
        if guess > secret:
            return "Too High", "📈 Go HIGHER!"
        else:
            return "Too Low", "📉 Go LOWER!"
    except TypeError:
        g = str(guess)
        if g == secret:
            return "Win", "🎉 Correct!"
        if g > secret:
            return "Too High", "📈 Go HIGHER!"
        return "Too Low", "📉 Go LOWER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    # BUG FIX (Bug 3b): attempts started at 1 before any guess was made, so
    # "Attempts left" was always one short (e.g. Easy showed 5 instead of 6).
    # CHANGED: start at 0 — no attempts have been used yet. This also matches
    # the New Game handler, which already resets attempts to 0.
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

st.subheader("Make a guess")

st.info(
    # BUG FIX (Bug 3a): the range was hard-coded as "1 and 100", so every
    # difficulty showed the same range on the main screen.
    # CHANGED: use {low} and {high} (from get_range_for_difficulty) so the
    # displayed range matches the selected difficulty (Easy 1-20, Hard 1-50).
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

# BUG FIX (Bug 2): the "Show hint" checkbox did nothing on its own.
# Previously `show_hint` was only used inside the `if submit:` block, so just
# checking/unchecking the box (which triggers a rerun without a submit) showed
# nothing. NEW: render a standalone hint here, outside of submit, so toggling
# the checkbox always produces visible feedback.
if show_hint:
    attempts_left = attempt_limit - st.session_state.attempts
    st.info(
        f"💡 Hint: The secret is between {low} and {high}. "
        f"You have {attempts_left} attempt(s) left."
    )

if new_game:
    # BUG FIX (Bug 1): "New Game" did not fully reset the game.
    # Previously this block only reset `attempts` and `secret`, so after a
    # win/loss the leftover state made the new game look frozen and kept the
    # old score/history. We now reset every piece of game state.

    st.session_state.attempts = 0  # unchanged: start fresh with 0 attempts used

    # CHANGED: use the difficulty range (low/high) instead of hard-coded 1, 100
    # so the new secret matches the selected difficulty (Easy 1-20, Hard 1-50).
    st.session_state.secret = random.randint(low, high)

    # NEW: reset status back to "playing". This is the key fix — without it,
    # the status stayed "won"/"lost" and the check below called st.stop(),
    # so the new game never actually started.
    st.session_state.status = "playing"

    # NEW: clear score and guess history so the old game doesn't carry over.
    st.session_state.score = 0
    st.session_state.history = []

    # BUG FIX (Bug 1, follow-up): resetting session state alone was NOT enough.
    # The guess text box is a keyed widget, so Streamlit kept its old value
    # across the rerun — after "New Game" the previous guess (e.g. "42") still
    # sat in the input, making the game look like it never reset. Deleting the
    # widget's key here clears it; on the rerun the input is recreated empty.
    input_key = f"guess_input_{difficulty}"
    if input_key in st.session_state:
        del st.session_state[input_key]

    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)

        # BUG FIX (Bug 4b): on even attempts the secret was converted to a
        # string, so check_guess compared int vs str, hit a TypeError, and fell
        # back to comparing them LEXICALLY (e.g. "9" > "50" -> "Too High").
        # That made the higher/lower feedback wrong every other turn.
        # CHANGED: always compare against the real int secret.
        secret = st.session_state.secret

        outcome, message = check_guess(guess_int, secret)

        # BUG FIX (Bug 4a): the higher/lower message is the core feedback that
        # tells you which way to go, but it only showed when "Show hint" was
        # checked. Unchecking the box left a submitted guess with no feedback at
        # all. CHANGED: always show the directional result; the hint checkbox
        # only controls the extra standalone hint above, not this message.
        st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
