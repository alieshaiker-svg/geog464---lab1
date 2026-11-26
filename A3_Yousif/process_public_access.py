"""Join playgrounds to official park records by INDEX_PARC / NUM_INDEX.

municipal_public_space describes cadastral ownership in the source dataset; it
does not guarantee legal, unrestricted, or 24-hour public access.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.validation import explain_validity


DATA_DIR = Path(__file__).resolve().parent / "data"
PLAYGROUNDS_PATH = DATA_DIR / "playgrounds_canopy.geojson"
PUBLIC_SPACES_PATH = DATA_DIR / "espace_vert.json"
OUTPUT_PATH = DATA_DIR / "playgrounds_public_access.geojson"
CONTEXT_FIELDS = ["Nom", "NUM_INDEX", "PROPRIETE", "GESTION", "COMPETENCE", "TYPO1", "TYPO2"]
ACCESS_CLASSES = [
    "municipal_public_space",
    "school_property",
    "institutional",
    "private",
    "other",
    "unknown",
]


def clean_key(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value or None


def clean_value(value):
    if pd.isna(value) or (isinstance(value, str) and not value.strip()):
        return None
    return value


def classify_access(owner):
    if owner is None or pd.isna(owner):
        return "unknown"
    return {
        "Ville de Montréal": "municipal_public_space",
        "Commission scolaire": "school_property",
        "Institutionnel": "institutional",
        "Privé": "private",
    }.get(owner, "other")


def context_signature(record):
    return tuple(clean_value(record[field]) for field in CONTEXT_FIELDS)


def main():
    playgrounds = gpd.read_file(PLAYGROUNDS_PATH)
    spaces = gpd.read_file(PUBLIC_SPACES_PATH)

    if playgrounds.crs is None:
        playgrounds = playgrounds.set_crs("EPSG:4326")
    if spaces.crs is None:
        spaces = spaces.set_crs("EPSG:4326")
    if spaces.crs != playgrounds.crs:
        spaces = spaces.to_crs(playgrounds.crs)

    source_fields = [
        field for field in playgrounds.columns if field != playgrounds.geometry.name
    ]
    playgrounds["_join_key"] = playgrounds["INDEX_PARC"].map(clean_key)
    spaces["_join_key"] = spaces["NUM_INDEX"].map(clean_key)

    lookup = {
        key: group
        for key, group in spaces.loc[spaces["_join_key"].notna()].groupby(
            "_join_key", sort=False
        )
    }

    # Spatial matching validates the ID join and resolves conflicting duplicate IDs only.
    spatial = gpd.sjoin(
        playgrounds,
        spaces[["NUM_INDEX", "Nom", "geometry"]],
        how="left",
        predicate="within",
    )
    if spatial.index.has_duplicates:
        duplicates = spatial.index[spatial.index.duplicated()].unique().tolist()
        raise ValueError(
            "A playground falls within multiple polygons; "
            f"review the ambiguous spatial matches: {duplicates}"
        )
    spatial = spatial.reindex(playgrounds.index)

    records = []
    key_matched = []
    conflict_resolutions = []
    for index, point in playgrounds.iterrows():
        key = point["_join_key"]
        group = lookup.get(key) if key is not None else None
        selected = None

        if group is not None:
            signatures = {context_signature(record) for _, record in group.iterrows()}
            if len(signatures) == 1:
                selected = group.iloc[0]
            else:
                spatial_index = spatial.loc[index, "index_right"]
                if pd.isna(spatial_index) or spatial_index not in group.index:
                    raise ValueError(
                        f"Conflicting records for NUM_INDEX {key} could not be "
                        "resolved by the containing polygon."
                    )
                selected = spaces.loc[int(spatial_index)]
                if clean_key(selected["NUM_INDEX"]) != key:
                    raise ValueError(
                        f"The spatial tie-break did not match INDEX_PARC {key}."
                    )
                conflict_resolutions.append(
                    (point["ID"], key, selected.get("OBJECTID"))
                )

        key_matched.append(selected is not None)
        record = {
            field: clean_value(selected[field]) if selected is not None else None
            for field in CONTEXT_FIELDS
        }
        record["public_space_name"] = record.pop("Nom")
        record["public_space_id"] = record.pop("NUM_INDEX")
        record["access_class"] = classify_access(record["PROPRIETE"])
        records.append(record)

    matched_context = pd.DataFrame(records, index=playgrounds.index)
    result = playgrounds.drop(columns=["_join_key"]).copy()
    output_fields = [
        "public_space_name",
        "public_space_id",
        "access_class",
        "PROPRIETE",
        "GESTION",
        "COMPETENCE",
        "TYPO1",
        "TYPO2",
    ]
    for field in output_fields:
        result[field] = matched_context[field]

    if not set(source_fields).issubset(result.columns):
        raise ValueError("The output is missing one or more original playground fields.")
    if len(result) != len(playgrounds):
        raise ValueError("The output feature count does not match the input.")

    key_matched = pd.Series(key_matched, index=playgrounds.index)
    input_keys = playgrounds["_join_key"]
    spatial_keys = spatial["NUM_INDEX"].map(clean_key)
    id_agrees = key_matched & spatial_keys.notna() & (input_keys == spatial_keys)
    id_differs = key_matched & spatial_keys.notna() & (input_keys != spatial_keys)
    id_missing_spatially = key_matched & spatial_keys.isna()
    unmatched_with_spatial_id = ~key_matched & spatial_keys.notna()
    unmatched_without_spatial_id = ~key_matched & spatial_keys.isna()

    boundary_matches = gpd.sjoin(
        playgrounds,
        spaces[["geometry"]],
        how="inner",
        predicate="touches",
    )
    intersection_matches = gpd.sjoin(
        playgrounds,
        spaces[["geometry"]],
        how="inner",
        predicate="intersects",
    )
    duplicate_intersection_points = int(
        (intersection_matches.groupby(level=0).size() > 1).sum()
    )
    invalid_spaces = spaces[~spaces.geometry.is_valid]
    missing_playground_geometries = int(playgrounds.geometry.isna().sum())
    empty_playground_geometries = int(playgrounds.geometry.is_empty.sum())
    missing_space_geometries = int(spaces.geometry.isna().sum())
    empty_space_geometries = int(spaces.geometry.is_empty.sum())
    invalid_playground_geometries = int(
        (playgrounds.geometry.notna() & ~playgrounds.geometry.is_valid).sum()
    )
    invalid_space_indices = set(invalid_spaces.index)
    invalid_polygon_matches = int(
        spatial["index_right"].isin(invalid_space_indices).sum()
    )

    output_path = OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_file(output_path, driver="GeoJSON", index=False)
    written = gpd.read_file(output_path)
    required_fields = source_fields + output_fields
    if len(written) != len(playgrounds):
        raise ValueError("The written output failed its feature-count check.")
    if not set(required_fields).issubset(written.columns):
        raise ValueError("The written output failed its property-preservation check.")
    if not set(written["access_class"].unique()).issubset(ACCESS_CLASSES):
        raise ValueError("The written output contains an unexpected access_class value.")

    class_counts = written["access_class"].value_counts().reindex(
        ACCESS_CLASSES, fill_value=0
    )
    municipal_named = int(
        (
            written["access_class"].eq("municipal_public_space")
            & written["public_space_name"].notna()
            & written["public_space_name"].astype(str).str.strip().ne("")
        ).sum()
    )
    duplicate_records = spaces.loc[
        spaces["_join_key"].notna()
        & spaces["_join_key"].duplicated(keep=False)
    ]
    duplicate_keys = set(duplicate_records["_join_key"])
    duplicate_playgrounds = playgrounds["_join_key"].isin(duplicate_keys)
    conflicting_keys = [
        key
        for key, group in duplicate_records.groupby("_join_key")
        if len({context_signature(record) for _, record in group.iterrows()}) > 1
    ]
    unmatched_keys = playgrounds.loc[~key_matched, "INDEX_PARC"].value_counts(
        dropna=False
    )

    print(f"Output: {output_path}")
    print(f"CRS: playgrounds={playgrounds.crs}; public spaces={spaces.crs}")
    print(f"Total playgrounds: {len(written)}")
    print("Counts by access_class:")
    for access_class in ACCESS_CLASSES:
        print(f"  {access_class}: {class_counts[access_class]}")
    print(f"INDEX_PARC matched to NUM_INDEX: {int(key_matched.sum())}/{len(written)}")
    print(f"Unmatched INDEX_PARC values: {unmatched_keys.to_dict()}")
    print(f"Municipal playgrounds with a nonblank official name: {municipal_named}")
    print(
        f"Duplicate NUM_INDEX records: {len(duplicate_records)} rows "
        f"across {len(duplicate_keys)} keys"
    )
    print(
        f"Playgrounds using duplicate keys: {int(duplicate_playgrounds.sum())} "
        f"features across {playgrounds.loc[duplicate_playgrounds, '_join_key'].nunique()} keys"
    )
    print(f"Conflicting duplicate NUM_INDEX keys in source: {conflicting_keys}")
    print(
        "Conflicts resolved by the unique containing polygon "
        f"(playground ID, NUM_INDEX, selected OBJECTID): {conflict_resolutions}"
    )

    print("\nID-join versus point-in-polygon validation:")
    print(f"Containing polygons found: {int(spatial['index_right'].notna().sum())}")
    print(f"Joined IDs agreeing with containing-polygon NUM_INDEX: {int(id_agrees.sum())}")
    print(f"Joined IDs with null containing-polygon NUM_INDEX: {int(id_missing_spatially.sum())}")
    print(f"Joined IDs differing from containing-polygon NUM_INDEX: {int(id_differs.sum())}")
    print(f"Unmatched ID joins with a spatial NUM_INDEX: {int(unmatched_with_spatial_id.sum())}")
    print(f"Unmatched ID joins with null spatial NUM_INDEX: {int(unmatched_without_spatial_id.sum())}")
    for index in playgrounds.index[id_differs]:
        print(
            "  ID disagreement:",
            {
                "playground_ID": playgrounds.loc[index, "ID"],
                "INDEX_PARC": playgrounds.loc[index, "INDEX_PARC"],
                "ID-join_name": result.loc[index, "public_space_name"],
                "ID-join_NUM_INDEX": result.loc[index, "public_space_id"],
                "spatial_name": spatial.loc[index, "Nom"],
                "spatial_NUM_INDEX": spatial.loc[index, "NUM_INDEX"],
            },
        )

    samples = written.loc[
        written["access_class"] == "municipal_public_space",
        ["ID", "ARROND", "public_space_name", "PROPRIETE", "canopy_pct_250m"],
    ].head(10)
    print("\nSample municipal public-space records:")
    print(samples.to_string(index=False))

    print("\nGeometry checks:")
    print(f"Points exactly on polygon boundaries: {boundary_matches.index.nunique()}")
    print(f"Points intersecting multiple polygons: {duplicate_intersection_points}")
    print(f"Playground geometries missing: {missing_playground_geometries}")
    print(f"Playground geometries empty: {empty_playground_geometries}")
    print(f"Playground geometries invalid: {invalid_playground_geometries}")
    print(f"Public-space geometries missing: {missing_space_geometries}")
    print(f"Public-space geometries empty: {empty_space_geometries}")
    print(f"Public-space geometries invalid: {len(invalid_spaces)}")
    print(f"Playgrounds matched to invalid polygons: {invalid_polygon_matches}")
    for _, feature in invalid_spaces.iterrows():
        print(
            "Invalid polygon:",
            {
                "OBJECTID": feature.get("OBJECTID"),
                "Nom": feature.get("Nom"),
                "NUM_INDEX": feature.get("NUM_INDEX"),
                "reason": explain_validity(feature.geometry),
            },
        )


if __name__ == "__main__":
    main()
