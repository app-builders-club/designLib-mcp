import pytest
from pydantic import ValidationError

from designlib_mcp.models.icon import Icon, IconSummary, IconFacets
from designlib_mcp.models.common import ResponseMeta


def test_summary_minimal():
    s = IconSummary(
        id="icon_phosphor_list",
        icon_name="list",
        category="Navigation",
        library_name="Phosphor",
    )
    assert s.style is None


def test_full_forbids_extra():
    with pytest.raises(ValidationError):
        Icon(
            id="x", category="Navigation", icon_name="list",
            library_name="Phosphor",
            import_code="import { List } from '@phosphor-icons/react'",
            usage="<List size={20} />",
            bogus="nope",
            meta=ResponseMeta(entity_type="icon"),
        )


def test_full_library_id_optional():
    i = Icon(
        id="icon_custom_anchor", category="Actions", icon_name="anchor",
        library_name="CustomSet", import_code="", usage="",
        meta=ResponseMeta(entity_type="icon"),
    )
    assert i.library_id is None


def test_facets_shape():
    f = IconFacets(
        categories=[{"value": "Navigation", "count": 10}],
        libraries=[{"value": "Phosphor", "count": 50}],
        styles=[{"value": "Outline", "count": 80}],
        meta=ResponseMeta(entity_type="icon_facets"),
    )
    assert len(f.categories) == 1
