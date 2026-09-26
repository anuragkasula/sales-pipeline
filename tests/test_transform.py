from pipeline.transform import clean, revenue_by_region


def test_clean_drops_malformed_and_blank_region():
    rows = [
        {"region": "north", "amount": "10"},
        {"region": "west", "amount": "oops"},
        {"region": "", "amount": "5"},
    ]
    assert clean(rows) == [{"region": "North", "amount": 10.0}]


def test_clean_normalises_region():
    assert clean([{"region": "  south ", "amount": "1"}])[0]["region"] == "South"


def test_clean_respects_min_amount():
    rows = [{"region": "east", "amount": "3"}, {"region": "east", "amount": "10"}]
    assert clean(rows, min_amount=5) == [{"region": "East", "amount": 10.0}]


def test_revenue_by_region_sums_and_sorts():
    rows = [
        {"region": "North", "amount": 1.1},
        {"region": "East", "amount": 2},
        {"region": "North", "amount": 2.2},
    ]
    assert revenue_by_region(rows) == {"East": 2.0, "North": 3.3}
