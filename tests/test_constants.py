from poe.constants import CLAUDE_SUBFOLDER, POB_XML_EXTENSION
from poe.services.repoe.constants import DEFAULT_ILVL, DEFAULT_ITERATIONS


def test_default_ilvl():
    assert DEFAULT_ILVL == 84


def test_default_iterations():
    assert DEFAULT_ITERATIONS == 10000


def test_claude_subfolder():
    assert CLAUDE_SUBFOLDER == "Claude"


def test_pob_xml_extension():
    assert POB_XML_EXTENSION == ".xml"
