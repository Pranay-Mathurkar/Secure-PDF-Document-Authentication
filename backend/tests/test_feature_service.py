"""Phase 6 tests for structural document feature extraction."""
import numpy as np

from app.services.feature_service import (
    analyze_feature_pages,
    calculate_canny_edges,
    calculate_edge_density,
    calculate_sobel_edges,
    compare_edge_maps,
    extract_document_feature_vector,
)


def _document_image() -> np.ndarray:
    image = np.full((64, 64), 255, dtype=np.uint8)
    image[10:54, 14:18] = 0
    image[10:14, 14:48] = 0
    image[30:34, 14:42] = 0
    return image


def test_sobel_returns_horizontal_vertical_and_combined_gradients():
    result = calculate_sobel_edges(_document_image())

    assert set(result) == {"horizontal_gradient", "vertical_gradient", "magnitude"}
    assert result["magnitude"].shape == (64, 64)
    assert np.max(result["magnitude"]) > 0


def test_canny_and_density_return_normalized_edges():
    edges = calculate_canny_edges(_document_image())

    assert edges.dtype == np.uint8
    assert set(np.unique(edges)).issubset({0, 255})
    assert 0.0 < calculate_edge_density(edges) < 1.0


def test_edge_similarity_is_perfect_for_identical_maps():
    edges = calculate_canny_edges(_document_image())

    assert compare_edge_maps(edges, edges.copy()) == 100.0


def test_changed_and_added_content_change_edge_features():
    reference = _document_image()
    changed = reference.copy()
    changed[20:24, 22:26] = 180
    added = reference.copy()
    added[48:58, 42:58] = 0

    reference_features = extract_document_feature_vector(reference)
    changed_features = extract_document_feature_vector(changed)
    added_features = extract_document_feature_vector(added)

    changed_similarity = compare_edge_maps(
        reference_features["edge_map"], changed_features["edge_map"]
    )
    added_similarity = compare_edge_maps(
        reference_features["edge_map"], added_features["edge_map"]
    )
    assert changed_features["edge_density"] != reference_features["edge_density"]
    assert added_features["edge_density"] != reference_features["edge_density"]
    assert 0 <= added_similarity < 100
    assert 0 <= changed_similarity < 100


def test_feature_vector_reuses_frequency_features_and_supports_pages():
    image = _document_image()
    result = analyze_feature_pages([image], [image.copy()])

    features = result["pages"][0]["features"]
    assert features["mean_intensity"] > 0
    assert "fft_features" in features
    assert "dct_features" in features
    assert result["pages"][0]["edge_similarity"] == 100.0
    assert result["overall_edge_similarity"] == 100.0
