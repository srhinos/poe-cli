from __future__ import annotations

from pydantic import BaseModel


class MasteryMapping(BaseModel):
    """A mastery effect selection: which effect is chosen on which node."""

    node_id: int
    effect_id: int


class TreeSocket(BaseModel):
    """A jewel socket on the passive tree, binding a node to an item."""

    node_id: int
    item_id: int


class TreeOverride(BaseModel):
    """A passive node overridden by a cluster jewel or timeless jewel."""

    node_id: int
    name: str
    icon: str = ""
    text: str = ""
    effect_image: str = ""


class TreeSpec(BaseModel):
    """A passive tree allocation stored in the build XML.

    Builds can have multiple specs (up to 16 in PoB). Each spec tracks
    allocated nodes, mastery choices, jewel sockets, and tree version.
    Parsed by xml.parser, written by xml.writer.
    """

    title: str = ""
    tree_version: str = ""
    nodes: list[int] = []
    url: str = ""
    class_id: int = 0
    ascend_class_id: int = 0
    secondary_ascend_class_id: int = 0
    mastery_effects: list[MasteryMapping] = []
    sockets: list[TreeSocket] = []
    overrides: list[TreeOverride] = []


class TreeSummary(BaseModel):
    """Compact spec info for TreeService.get_specs() listings.

    Intentionally lighter than TreeSpec — no node lists or mastery details,
    just enough to show in a spec picker.
    """

    index: int
    title: str
    tree_version: str = ""
    node_count: int = 0
    class_id: int = 0
    ascend_class_id: int = 0
    active: bool = False


class TreeSpecList(BaseModel):
    """Response from TreeService.get_specs() — all specs with active indicator."""

    active_spec: int
    specs: list[TreeSummary] = []


class TreeDetail(TreeSpec):
    """Full spec detail returned by TreeService.get_tree().

    Inherits all TreeSpec fields and adds context: which spec index this
    is and the computed node count.
    """

    spec_index: int
    node_count: int = 0


class TreeComparison(BaseModel):
    """Node-level diff between two builds, returned by TreeService.compare_trees().

    Splits nodes into build1-only, build2-only, and shared sets.
    Also diffs mastery selections and class/ascendancy choices.
    """

    build1_only: list[int] = []
    build2_only: list[int] = []
    shared: list[int] = []
    build1_count: int = 0
    build2_count: int = 0
    mastery_diff: dict = {}
    class_diff: dict = {}


class TreeDiff(BaseModel):
    """Directional diff (added/removed) between two tree specs."""

    added_nodes: list[int] = []
    removed_nodes: list[int] = []
    added_masteries: list[MasteryMapping] = []
    removed_masteries: list[MasteryMapping] = []
