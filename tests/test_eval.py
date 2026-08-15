from src.services.eval import load_golden_set


def test_load_golden_set():
    questions = load_golden_set()
    assert len(questions) >= 1
    assert questions[0].question
    assert questions[0].ground_truth
