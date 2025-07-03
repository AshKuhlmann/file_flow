from sorter import cli_utils


def test_human_readable_size():
    assert cli_utils.human_readable_size(1024) == "1.0 KB"
    assert cli_utils.human_readable_size(0) == "0.0 B"
    assert cli_utils.human_readable_size(1024 * 1024 * 5) == "5.0 MB"
