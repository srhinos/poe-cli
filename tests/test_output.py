import json

from pydantic import BaseModel

from poe.output import _format_dict_human, _format_human, _format_json, human_formatter, render


class SampleModel(BaseModel):
    name: str
    value: int
    optional: str | None = None


class TestFormatJson:
    def test_dict(self):
        result = _format_json({"key": "val"})
        assert json.loads(result) == {"key": "val"}

    def test_pydantic_model(self):
        m = SampleModel(name="test", value=42)
        result = _format_json(m)
        parsed = json.loads(result)
        assert parsed["name"] == "test"
        assert parsed["value"] == 42

    def test_pydantic_excludes_none(self):
        m = SampleModel(name="test", value=1, optional=None)
        result = _format_json(m)
        assert "optional" not in result

    def test_pydantic_list(self):
        items = [SampleModel(name="a", value=1), SampleModel(name="b", value=2)]
        result = _format_json(items)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["name"] == "a"
        assert parsed[1]["name"] == "b"

    def test_list_excludes_none(self):
        items = [SampleModel(name="a", value=1, optional=None)]
        result = _format_json(items)
        parsed = json.loads(result)
        assert "optional" not in parsed[0]


class TestFormatDictHuman:
    def test_simple_dict(self):
        result = _format_dict_human({"name": "test", "value": 42})
        assert "name: test" in result
        assert "value: 42" in result

    def test_nested_dict(self):
        result = _format_dict_human({"outer": {"inner": "val"}})
        assert "outer:" in result
        assert "  inner: val" in result

    def test_list_of_strings(self):
        result = _format_dict_human(["a", "b", "c"])
        assert "- a" in result
        assert "- b" in result

    def test_list_of_dicts(self):
        result = _format_dict_human([{"k": "v"}, {"k": "v2"}])
        assert "k: v" in result
        assert "k: v2" in result

    def test_scalar(self):
        result = _format_dict_human("hello")
        assert result == "hello"


class TestHumanFormatter:
    def test_registered_formatter(self):
        @human_formatter(SampleModel)
        def fmt(m):
            return f"{m.name} = {m.value}"

        result = _format_human(SampleModel(name="x", value=5))
        assert result == "x = 5"

    def test_registered_formatter_list(self):
        # Uses the formatter registered above
        items = [SampleModel(name="a", value=1), SampleModel(name="b", value=2)]
        result = _format_human(items)
        assert "a = 1" in result
        assert "b = 2" in result

    def test_dict_fallback(self):
        result = _format_human({"key": "val"})
        assert "key: val" in result


class TestRender:
    def test_render_json_dict(self, capsys):
        render({"x": 1}, human=False)
        captured = capsys.readouterr()
        assert json.loads(captured.out) == {"x": 1}

    def test_render_json_model(self, capsys):
        render(SampleModel(name="test", value=99), human=False)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["name"] == "test"

    def test_render_human_dict(self, capsys):
        render({"key": "val"}, human=True)
        captured = capsys.readouterr()
        assert "key: val" in captured.out

    def test_render_human_model(self, capsys):
        render(SampleModel(name="hi", value=7), human=True)
        captured = capsys.readouterr()
        assert "hi" in captured.out

    def test_render_unicode_characters(self, capsys):
        render({"name": "Black Mórrigan", "league": "Cola küsst Orange"})
        captured = capsys.readouterr()
        assert "Mórrigan" in captured.out
        assert "küsst" in captured.out
