"""Context enrichment - map user data to graph node IDs."""

def _to_node(prefix, val):
    c = str(val).strip().lower().replace(" ", "_")[:50]
    return prefix + ":" + c


def enrich_user_context(user):
    locs = user.get("locations") or []
    inds = user.get("industries") or []
    return {
        "location_nodes": [_to_node("loc", l) for l in locs if l],
        "industry_nodes": [_to_node("ind", i) for i in inds if i],
    }
