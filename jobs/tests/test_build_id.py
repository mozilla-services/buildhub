import pytest

from buildhub.check_missing_releases import build_record_id
from test_utils import RECORDS


# Build record_id from url
@pytest.mark.parametrize("record", RECORDS)
def test_build_record_id_from_url(record):
    record_id = build_record_id(record["download"]["url"])
    assert record_id == record["id"]
