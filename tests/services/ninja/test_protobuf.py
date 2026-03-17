from __future__ import annotations

from pathlib import Path

from poe.models.ninja.protobuf import Dictionary, NinjaSearchResult
from poe.services.ninja.protobuf import (
    decode_fields,
    decode_varint,
    get_all_messages,
    get_all_strings,
    get_all_varints,
    get_bool,
    get_bytes,
    get_double,
    get_map_string_string,
    get_string,
    get_varint,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestDecodeVarint:
    def test_single_byte(self):
        val, pos = decode_varint(b"\x05", 0)
        assert val == 5
        assert pos == 1

    def test_multi_byte(self):
        val, pos = decode_varint(b"\xac\x02", 0)
        assert val == 300
        assert pos == 2

    def test_with_offset(self):
        val, pos = decode_varint(b"\x00\x05", 1)
        assert val == 5
        assert pos == 2

    def test_zero(self):
        val, pos = decode_varint(b"\x00", 0)
        assert val == 0
        assert pos == 1


class TestDecodeFields:
    def test_varint_field(self):
        # field 1, wire type 0, value 150 -> tag=0x08, varint=0x96 0x01
        fields = decode_fields(b"\x08\x96\x01")
        assert len(fields) == 1
        fn, wt, val = fields[0]
        assert fn == 1
        assert wt == 0
        assert val == 150

    def test_string_field(self):
        # field 2, wire type 2, "testing"
        data = b"\x12\x07testing"
        fields = decode_fields(data)
        assert len(fields) == 1
        fn, wt, val = fields[0]
        assert fn == 2
        assert wt == 2
        assert val == b"testing"

    def test_multiple_fields(self):
        data = b"\x08\x01\x12\x03abc"
        fields = decode_fields(data)
        assert len(fields) == 2

    def test_empty_buffer(self):
        assert decode_fields(b"") == []


class TestHelpers:
    def test_get_varint(self):
        fields = decode_fields(b"\x08\x2a")
        assert get_varint(fields, 1) == 42
        assert get_varint(fields, 2) == 0
        assert get_varint(fields, 2, 99) == 99

    def test_get_bool(self):
        fields = decode_fields(b"\x08\x01")
        assert get_bool(fields, 1) is True
        assert get_bool(fields, 2) is False

    def test_get_string(self):
        fields = decode_fields(b"\x12\x05hello")
        assert get_string(fields, 2) == "hello"
        assert get_string(fields, 3) == ""
        assert get_string(fields, 3, "default") == "default"

    def test_get_double(self):
        import struct

        double_bytes = struct.pack("<d", 12.5)
        # field 2, wire type 1
        data = b"\x11" + double_bytes
        fields = decode_fields(data)
        assert get_double(fields, 2) == 12.5
        assert get_double(fields, 3) == 0.0

    def test_get_bytes(self):
        fields = decode_fields(b"\x12\x03abc")
        assert get_bytes(fields, 2) == b"abc"
        assert get_bytes(fields, 3) is None

    def test_get_all_messages(self):
        data = b"\x12\x01a\x12\x01b"
        fields = decode_fields(data)
        msgs = get_all_messages(fields, 2)
        assert len(msgs) == 2
        assert msgs[0] == b"a"
        assert msgs[1] == b"b"

    def test_get_all_strings(self):
        data = b"\x12\x03foo\x12\x03bar"
        fields = decode_fields(data)
        assert get_all_strings(fields, 2) == ["foo", "bar"]

    def test_get_all_varints_unpacked(self):
        data = b"\x08\x01\x08\x02\x08\x03"
        fields = decode_fields(data)
        assert get_all_varints(fields, 1) == [1, 2, 3]

    def test_get_all_varints_packed(self):
        # field 3, wire type 2, packed varints [1, 2, 3]
        data = b"\x1a\x03\x01\x02\x03"
        fields = decode_fields(data)
        assert get_all_varints(fields, 3) == [1, 2, 3]

    def test_get_map_string_string(self):
        # map entry: field 7, wire type 2, containing field 1="key" and field 2="val"
        entry = b"\x0a\x03key\x12\x03val"
        data = b"\x3a" + bytes([len(entry)]) + entry
        fields = decode_fields(data)
        assert get_map_string_string(fields, 7) == {"key": "val"}


class TestNinjaSearchResult:
    def test_decode_fixture(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        msg = NinjaSearchResult.from_protobuf(data)

        assert msg.result is not None
        assert msg.result.total == 124428
        assert len(msg.result.dimensions) == 2
        assert msg.result.dimensions[0].id == "class"
        assert msg.result.dimensions[0].dictionary_id == "dict-class"
        assert len(msg.result.dimensions[0].counts) == 2
        assert msg.result.dimensions[0].counts[0].key == 0
        assert msg.result.dimensions[0].counts[0].count == 15234

    def test_integer_dimensions(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        msg = NinjaSearchResult.from_protobuf(data)

        assert len(msg.result.integer_dimensions) == 2
        level_dim = msg.result.integer_dimensions[0]
        assert level_dim.id == "level"
        assert level_dim.min_value == 70
        assert level_dim.max_value == 100

    def test_dictionary_references(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        msg = NinjaSearchResult.from_protobuf(data)

        assert len(msg.result.dictionaries) == 2
        assert msg.result.dictionaries[0].id == "dict-class"
        assert msg.result.dictionaries[0].hash == "abc123"

    def test_value_lists(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        msg = NinjaSearchResult.from_protobuf(data)

        assert len(msg.result.value_lists) == 1
        vl = msg.result.value_lists[0]
        assert vl.id == "names"
        assert len(vl.values) == 2
        assert vl.values[0].str_val == "TestChar1"

    def test_fields_and_sections(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        msg = NinjaSearchResult.from_protobuf(data)

        assert len(msg.result.fields) == 1
        assert msg.result.fields[0].id == "name"
        assert len(msg.result.sections) == 1
        assert msg.result.sections[0].id == "main"
        assert len(msg.result.field_descriptors) == 1
        assert msg.result.default_field_ids == ["name"]

    def test_performance_points(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        msg = NinjaSearchResult.from_protobuf(data)

        assert len(msg.result.performance_points) == 1
        assert msg.result.performance_points[0].name == "query"
        assert msg.result.performance_points[0].ms == 12.5

    def test_empty_message(self):
        msg = NinjaSearchResult.from_protobuf(b"")
        assert msg.result is None

    def test_is_pydantic(self):
        from pydantic import BaseModel

        assert issubclass(NinjaSearchResult, BaseModel)
        msg = NinjaSearchResult.from_protobuf(b"")
        assert isinstance(msg, BaseModel)

    def test_serializes_to_json(self):
        data = (FIXTURES / "search_result.bin").read_bytes()
        msg = NinjaSearchResult.from_protobuf(data)
        json_str = msg.model_dump_json()
        assert "124428" in json_str
        assert "dict-class" in json_str


class TestDictionary:
    def test_decode_fixture(self):
        data = (FIXTURES / "dictionary.bin").read_bytes()
        d = Dictionary.from_protobuf(data)

        assert d.id == "class"
        assert d.values == ["Pathfinder", "Necromancer", "Deadeye", "Champion"]
        assert len(d.properties) == 1
        assert d.properties[0].id == "color"
        assert len(d.properties[0].values) == 4

    def test_is_pydantic(self):
        from pydantic import BaseModel

        assert issubclass(Dictionary, BaseModel)
