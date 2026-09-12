"""Tests for the nixos-survey-limesurvey console script."""

from nixos_survey_lib.cli import main


def test_writes_output_file(fixtures_dir, tmp_path):
    """With -o the TSV goes to that file, byte-identical to to_tsv's output
    (the golden file), including the byte-order mark."""
    out = tmp_path / "survey.txt"
    rc = main([str(fixtures_dir / "limesurvey" / "survey.toml"), "-o", str(out)])
    assert rc == 0
    expected = (fixtures_dir / "limesurvey" / "expected_survey.txt").read_bytes()
    assert out.read_bytes() == expected


def test_writes_stdout_when_no_output_given(fixtures_dir, capsysbinary):
    """Without -o the same bytes go to stdout, so the script composes with
    shell redirection."""
    rc = main([str(fixtures_dir / "limesurvey" / "survey.toml")])
    assert rc == 0
    expected = (fixtures_dir / "limesurvey" / "expected_survey.txt").read_bytes()
    assert capsysbinary.readouterr().out == expected


def test_validation_error_is_reported_not_raised(tmp_path, capsys):
    """A SurveyError becomes a one-line message on stderr and exit code 1,
    not a traceback."""
    (tmp_path / "survey.toml").write_text("[survey]\nid = 1\n", encoding="utf-8")
    rc = main([str(tmp_path / "survey.toml")])
    assert rc == 1
    err = capsys.readouterr().err
    assert "survey.toml" in err
