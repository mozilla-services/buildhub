import pytest
from buildhub.index_filters import build_version_id


VERSIONS = [
    ('54.0b1', '054000000b001'),
    ('53.0b99', '053000000b099'),
    ('45.9.0esr', '045009000x000'),
    ('54.0a2', '054000000a002'),
    ('54.0.1a2', '054000001a002'),
    ('2.48b1', '002048000b001'),
    ('2.48.3b1', '002048003b001'),
    ('50.0.1', '050000001r000'),
    ('50.0', '050000000r000'),
    ('50.0esr', '050000000x000'),
    ('50.0.12esr', '050000012x000'),
    ('2.50a1', '002050000a001'),
]


@pytest.mark.parametrize("arg,output", VERSIONS)
def test_parse_nightly_filename_raise_a_value_error(arg, output):
    assert build_version_id(arg) == output
