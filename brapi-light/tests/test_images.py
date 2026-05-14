"""
Feature: Images
  As a Field Book Android client
  I want to upload image metadata and content
  So that field photos sync to the server

  Scenario: POST creates image metadata record
    Given a valid image metadata payload
    When POST /brapi/v2/images is called
    Then returns the created image with server-generated imageDbId

  Scenario: PUT uploads image content
    Given an image metadata record exists
    When PUT /brapi/v2/images/{id}/imagecontent with binary data
    Then stores the content and returns the updated image

  Scenario: PUT returns 404 for unknown image
    Given no image with the given ID
    When PUT /brapi/v2/images/{id}/imagecontent
    Then returns 404
"""

import pytest


@pytest.mark.asyncio
async def test_images_post_metadata(client, db_session):
    from brapi_light.models.core import Program, Study, Trial
    from brapi_light.models.phenotyping import ObservationUnit

    p = Program(program_db_id="p1", program_name="Wheat")
    t = Trial(trial_db_id="t1", trial_name="T1", program_db_id="p1")
    s = Study(study_db_id="s1", study_name="S1", program_db_id="p1", trial_db_id="t1")
    u = ObservationUnit(observation_unit_db_id="u1", study_db_id="s1")
    db_session.add_all([p, t, s, u])
    await db_session.commit()

    response = await client.post("/brapi/v2/images", json=[{
        "observationUnitDbId": "u1",
        "imageFileName": "photo.jpg",
        "imageName": "Plot Photo",
        "mimeType": "image/jpeg",
        "imageFileSize": 1024,
    }])
    assert response.status_code == 200
    data = response.json()["result"]["data"]
    assert len(data) == 1
    assert data[0]["imageDbId"] is not None
    assert data[0]["imageFileName"] == "photo.jpg"


@pytest.mark.asyncio
async def test_images_put_content(client, db_session):
    from brapi_light.models.phenotyping import Image

    img = Image(image_db_id="img1", image_file_name="test.jpg", mime_type="image/jpeg")
    db_session.add(img)
    await db_session.commit()

    response = await client.put(
        "/brapi/v2/images/img1/imagecontent",
        content=b"\x89PNG fake image data",
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200
    assert response.json()["result"]["imageDbId"] == "img1"


@pytest.mark.asyncio
async def test_images_put_content_404(client):
    response = await client.put(
        "/brapi/v2/images/nonexistent/imagecontent",
        content=b"data",
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_images_get_list_empty(client):
    """GET /images returns empty paginated list when no images exist."""
    response = await client.get("/brapi/v2/images")
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["data"] == []
    assert body["metadata"]["pagination"]["totalCount"] == 0


@pytest.mark.asyncio
async def test_images_get_list_filtered(client, db_session):
    """GET /images with observationUnitDbId filter returns matching images."""
    from brapi_light.models.core import Program, Study, Trial
    from brapi_light.models.phenotyping import Image, ObservationUnit

    p = Program(program_db_id="p2", program_name="Barley")
    t = Trial(trial_db_id="t2", trial_name="T2", program_db_id="p2")
    s = Study(study_db_id="s2", study_name="S2", program_db_id="p2", trial_db_id="t2")
    u1 = ObservationUnit(observation_unit_db_id="u2a", study_db_id="s2")
    u2 = ObservationUnit(observation_unit_db_id="u2b", study_db_id="s2")
    img1 = Image(image_db_id="imga", observation_unit_db_id="u2a", image_file_name="a.jpg")
    img2 = Image(image_db_id="imgb", observation_unit_db_id="u2b", image_file_name="b.jpg")
    db_session.add_all([p, t, s, u1, u2, img1, img2])
    await db_session.commit()

    response = await client.get("/brapi/v2/images", params={"observationUnitDbId": "u2a"})
    assert response.status_code == 200
    data = response.json()["result"]["data"]
    assert len(data) == 1
    assert data[0]["imageDbId"] == "imga"


@pytest.mark.asyncio
async def test_images_get_single(client, db_session):
    """GET /images/{imageDbId} returns single image metadata (no content)."""
    from brapi_light.models.phenotyping import Image

    img = Image(image_db_id="img2", image_file_name="test.png", mime_type="image/png",
                image_file_size=2048, image_name="Test")
    db_session.add(img)
    await db_session.commit()

    response = await client.get("/brapi/v2/images/img2")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["imageDbId"] == "img2"
    assert result["imageFileName"] == "test.png"
    assert "content" not in result


@pytest.mark.asyncio
async def test_images_get_content(client, db_session):
    """GET /images/{imageDbId}/imagecontent returns the binary content."""
    from brapi_light.models.phenotyping import Image

    img = Image(image_db_id="img3", image_file_name="photo.jpg", mime_type="image/jpeg",
                content=b"\x89PNG\x00\x01")
    db_session.add(img)
    await db_session.commit()

    response = await client.get("/brapi/v2/images/img3/imagecontent")
    assert response.status_code == 200
    assert response.content == b"\x89PNG\x00\x01"
    assert response.headers["content-type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_images_get_content_404(client):
    """GET /images/{imageDbId}/imagecontent returns 404 for unknown image."""
    response = await client.get("/brapi/v2/images/nonexistent/imagecontent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_images_put_metadata(client, db_session):
    """PUT /images/{imageDbId} updates image metadata fields."""
    from brapi_light.models.phenotyping import Image

    img = Image(image_db_id="img4", image_file_name="old.jpg", image_name="Old",
                description="before", mime_type="image/jpeg")
    db_session.add(img)
    await db_session.commit()

    response = await client.put("/brapi/v2/images/img4", json={
        "imageFileName": "new.jpg",
        "imageName": "New",
        "description": "after",
    })
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["imageFileName"] == "new.jpg"
    assert result["imageName"] == "New"
    assert result["description"] == "after"
    assert result["mimeType"] == "image/jpeg"  # unchanged
    assert "content" not in result


@pytest.mark.asyncio
async def test_images_put_metadata_404(client):
    """PUT /images/{imageDbId} returns 404 for unknown image."""
    response = await client.put("/brapi/v2/images/nonexistent", json={
        "imageFileName": "x.jpg",
    })
    assert response.status_code == 404
