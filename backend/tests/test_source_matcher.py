"""Research tooling is optional in runtime, but checked when installed in CI."""

from scripts.source_neet_answers import (
    option_mapping,
    parse_key,
    parse_options,
    option_normal,
)


def test_option_mapping_preserves_signs_decimals_and_semantic_distractors():
    source = {"A": "4.4 mT", "B": "44 T", "C": "44 mT", "D": "4.4 T"}
    target = {"A": "44 mT", "B": "4.4 mT", "C": "4.4 T", "D": "44 T"}
    mapping = option_mapping(target, source)
    assert mapping["B"]["source_option"] == "A"
    assert len(mapping) == 4
    assert option_normal("-30 J") != option_normal("30 J")
    assert option_normal("4.4 mT") != option_normal("44 mT")
    assert not option_mapping(
        {"A": "Statement I is true but II is false"},
        {"B": "Statement I is false but II is true"},
    )
    assert not option_mapping({"A": "[image: diagrams/a.png]"}, {"A": "1.0"})


def test_ambiguous_options_do_not_get_assigned_by_position():
    assert not option_mapping({"A": "same", "B": "same"}, {"A": "same", "B": "same"})
    assert parse_key("1,2") == ["A", "B"]
    assert parse_key("None") == []
    assert parse_key("5") == []  # Dropped/bonus is not option A.
    stem, options = parse_options("Stem (1) red (2) blue (3) green (4) black")
    assert stem.strip() == "Stem" and options["B"] == "blue"
