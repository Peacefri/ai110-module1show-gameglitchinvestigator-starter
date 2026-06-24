"""Regression tests for the three bugs we fixed in app.py.

These bugs all live in the Streamlit app body (UI + session state), not in a
pure helper, so we drive the real app with Streamlit's official AppTest harness
(streamlit.testing.v1) and assert on widgets / session state.

Bug 1 -- "New Game" did not fully reset the game (status/score/history stuck).
Bug 2 -- "Show hint" checkbox did nothing unless you also submitted a guess.
Bug 3 -- Difficulty was not synced on the main screen:
         3a) range was hard-coded as "1 and 100" for every difficulty.
         3b) attempts started at 1, so "Attempts left" was always one short.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def _fresh_app():
    return AppTest.from_file(APP_PATH)


# ---------------------------------------------------------------------------
# Bug 1: "New Game" must reset ALL game state, not just attempts + secret.
# ---------------------------------------------------------------------------
def test_new_game_fully_resets_state():
    at = _fresh_app()

    # Simulate a finished game with leftover state (a win, points on the board,
    # used-up attempts, and a guess history).
    at.session_state["status"] = "won"
    at.session_state["score"] = 75
    at.session_state["attempts"] = 8
    at.session_state["history"] = [10, 20, 50]
    at.run(timeout=10)

    # Buttons are created in order: [0] = "Submit Guess", [1] = "New Game".
    # The handler calls st.rerun(), so give this run extra time.
    at.button[1].click().run(timeout=10)

    assert at.session_state["status"] == "playing", "status must reset to playing"
    assert at.session_state["attempts"] == 0, "attempts must reset to 0"
    assert at.session_state["score"] == 0, "score must reset to 0"
    assert at.session_state["history"] == [], "history must be cleared"

    # And because status is back to "playing", the app should NOT have stopped
    # early on the 'already won' / 'game over' branch.
    assert not at.exception


# ---------------------------------------------------------------------------
# Bug 1 (follow-up): "New Game" must also clear the guess input box. Resetting
# session state alone left the previous guess sitting in the keyed text widget,
# so in the browser the game looked like it never reset.
# ---------------------------------------------------------------------------
def test_new_game_clears_the_guess_input():
    at = _fresh_app()
    at.session_state["secret"] = 50
    at.run(timeout=10)

    # Play a real turn: type a guess and submit it.
    at.text_input[0].set_value("42")
    at.button[0].click().run(timeout=10)
    assert at.text_input[0].value == "42", "guess should be in the box after submitting"

    # Click "New Game" (button[1]); the input must come back empty.
    at.button[1].click().run(timeout=10)
    assert at.text_input[0].value == "", "New Game must clear the guess input box"
    assert not at.exception


# ---------------------------------------------------------------------------
# Bug 2: "Show hint" must produce visible feedback on its own (no submit).
# ---------------------------------------------------------------------------
def test_show_hint_checkbox_works_without_submitting():
    at = _fresh_app()
    at.run()

    # Checkbox defaults to True, so a standalone hint should already be visible.
    hint_shown = any("Hint:" in info.value for info in at.info)
    assert hint_shown, "hint should render when the box is checked, even without a submit"

    # Unchecking it (which only triggers a rerun, no submit) must hide the hint.
    at.checkbox[0].uncheck().run()
    hint_shown = any("Hint:" in info.value for info in at.info)
    assert not hint_shown, "hint must disappear when the box is unchecked"


# ---------------------------------------------------------------------------
# Bug 3: difficulty must be synced on the main screen (range + attempts-left).
# ---------------------------------------------------------------------------
def test_difficulty_range_and_attempts_are_synced():
    at = _fresh_app()
    at.run()

    # Switch to Easy: range should become 1..20 and attempt limit 6.
    at.sidebar.selectbox[0].set_value("Easy").run()
    main_text = " ".join(info.value for info in at.info)

    # Bug 3a: range on the main screen must match the difficulty, not "1 and 100".
    assert "between 1 and 20" in main_text, "Easy range should show 1..20, not 1..100"
    assert "between 1 and 100" not in main_text, "stale hard-coded 1..100 must be gone"

    # Bug 3b: with attempts starting at 0, Easy must show all 6 attempts left.
    assert at.session_state["attempts"] == 0, "no guesses made yet -> attempts must be 0"
    assert "Attempts left: 6" in main_text, "Easy should show 6 attempts left, not 5"

    # Sanity-check the other difficulties stay in sync too.
    at.sidebar.selectbox[0].set_value("Hard").run()
    main_text = " ".join(info.value for info in at.info)
    assert "between 1 and 50" in main_text, "Hard range should show 1..50"
    assert "Attempts left: 5" in main_text, "Hard should show 5 attempts left"


# ---------------------------------------------------------------------------
# Bug 4a: the higher/lower result is core feedback and must show after every
# submit, even when "Show hint" is unchecked (it used to be gated by the box).
# ---------------------------------------------------------------------------
def test_directional_feedback_shows_when_hint_is_off():
    at = _fresh_app()
    at.session_state["secret"] = 50  # known secret so the direction is fixed
    at.run()

    # Turn the hint off, then guess 9 (which is below the secret of 50).
    at.checkbox[0].uncheck()
    at.text_input[0].set_value("9")
    at.button[0].click()
    at.run()

    warnings = " ".join(w.value for w in at.warning)
    assert "LOWER" in warnings, (
        "directional feedback must still show after a guess even when the "
        "hint box is unchecked"
    )


# ---------------------------------------------------------------------------
# Bug 4b: on even attempts the secret was stringified, so check_guess compared
# lexically ("9" > "50" -> Too High). The direction must be numerically correct
# on every attempt, including even ones.
# ---------------------------------------------------------------------------
def test_even_attempt_feedback_is_numerically_correct():
    at = _fresh_app()
    at.session_state["secret"] = 50
    at.session_state["attempts"] = 1  # next submit makes attempts == 2 (even)
    at.run()

    at.text_input[0].set_value("9")
    at.button[0].click()
    at.run()

    assert at.session_state["attempts"] == 2, "this submit must land on an even attempt"
    warnings = " ".join(w.value for w in at.warning)
    assert "LOWER" in warnings, "9 is below 50, so even-attempt feedback must say LOWER"
    assert "HIGHER" not in warnings, "lexical 'too high' bug must be gone"
