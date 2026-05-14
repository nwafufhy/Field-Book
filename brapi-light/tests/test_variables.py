"""
Feature: Observation Variables (Traits)
  As a Field Book Android client
  I want to list observation variables (traits) for a study

  Scenario: Returns empty list when no variables seeded
    Given an empty database, When GET /brapi/v2/variables
    Then returns 200 with an empty data array

  Scenario: Returns variables filtered by studyDbId
    Given variables seeded for different studies
    When GET /brapi/v2/variables?studyDbId=S1 is called
    Then returns only variables belonging to study S1

  Scenario: Variable contains trait and scale info
    Given a variable is seeded with trait/scale JSON
    When GET /brapi/v2/variables is called
    Then each variable has observationVariableDbId, observationVariableName, trait, and scale

  Scenario: Supports pagination
    Given multiple variables seeded
    When GET /brapi/v2/variables?page=0&pageSize=1 is called
    Then returns one variable with correct pagination metadata
"""

import json
import pytest


@pytest.mark.asyncio
async def test_variables_empty_list(client):
    response = await client.get("/brapi/v2/variables")
    assert response.status_code == 200
    assert response.json()["result"]["data"] == []


@pytest.mark.asyncio
async def test_variables_filtered_by_study(client, db_session):
    from brapi_light.models.core import Program, Study, Trial
    from brapi_light.models.phenotyping import ObservationVariable

    p = Program(program_db_id="p1", program_name="Wheat")
    t = Trial(trial_db_id="t1", trial_name="T1", program_db_id="p1")
    s1 = Study(study_db_id="s1", study_name="S1", program_db_id="p1", trial_db_id="t1")
    s2 = Study(study_db_id="s2", study_name="S2", program_db_id="p1", trial_db_id="t1")
    db_session.add_all([p, t, s1, s2])
    await db_session.flush()
    db_session.add_all([
        ObservationVariable(observation_variable_db_id="v1", observation_variable_name="Height", study_db_id="s1"),
        ObservationVariable(observation_variable_db_id="v2", observation_variable_name="Yield", study_db_id="s1"),
        ObservationVariable(observation_variable_db_id="v3", observation_variable_name="Color", study_db_id="s2"),
    ])
    await db_session.commit()

    response = await client.get("/brapi/v2/variables?studyDbId=s1")
    assert response.status_code == 200
    data = response.json()["result"]["data"]
    assert len(data) == 2
    names = {v["observationVariableName"] for v in data}
    assert names == {"Height", "Yield"}


@pytest.mark.asyncio
async def test_variables_has_trait_and_scale(client, db_session):
    from brapi_light.models.core import Program, Study, Trial
    from brapi_light.models.phenotyping import ObservationVariable

    p = Program(program_db_id="p1", program_name="Wheat")
    t = Trial(trial_db_id="t1", trial_name="T1", program_db_id="p1")
    s = Study(study_db_id="s1", study_name="S1", program_db_id="p1", trial_db_id="t1")
    db_session.add_all([p, t, s])
    await db_session.flush()
    db_session.add(ObservationVariable(
        observation_variable_db_id="v1",
        observation_variable_name="Plant Height",
        study_db_id="s1",
        trait=json.dumps({"traitDescription": "Plant height measured in cm"}),
        scale=json.dumps({"dataType": "Numerical", "validValues": {"min": "0", "max": "300"}}),
    ))
    await db_session.commit()

    response = await client.get("/brapi/v2/variables")
    assert response.status_code == 200
    var = response.json()["result"]["data"][0]
    assert var["observationVariableDbId"] == "v1"
    assert var["observationVariableName"] == "Plant Height"
    assert var["trait"] == {"traitDescription": "Plant height measured in cm"}
    assert var["scale"]["dataType"] == "Numerical"


@pytest.mark.asyncio
async def test_variables_pagination(client, db_session):
    from brapi_light.models.core import Program, Study, Trial
    from brapi_light.models.phenotyping import ObservationVariable

    p = Program(program_db_id="p1", program_name="Wheat")
    t = Trial(trial_db_id="t1", trial_name="T1", program_db_id="p1")
    s = Study(study_db_id="s1", study_name="S1", program_db_id="p1", trial_db_id="t1")
    db_session.add_all([p, t, s])
    await db_session.flush()
    for i in range(5):
        db_session.add(ObservationVariable(
            observation_variable_db_id=f"v{i}", observation_variable_name=f"Var{i}", study_db_id="s1"
        ))
    await db_session.commit()

    response = await client.get("/brapi/v2/variables?page=0&pageSize=2")
    assert response.status_code == 200
    assert len(response.json()["result"]["data"]) == 2
    assert response.json()["metadata"]["pagination"]["totalCount"] == 5


@pytest.mark.asyncio
async def test_post_variables_creates_with_trait_and_scale(client, db_session):
    from brapi_light.models.core import Program, Study, Trial

    p = Program(program_db_id="p1", program_name="Wheat")
    t = Trial(trial_db_id="t1", trial_name="T1", program_db_id="p1")
    s = Study(study_db_id="s1", study_name="S1", program_db_id="p1", trial_db_id="t1")
    db_session.add_all([p, t, s])
    await db_session.commit()

    payload = [{
        "observationVariableName": "Plant Height",
        "studyDbId": "s1",
        "trait": {"traitName": "Plant Height", "traitDescription": "Height in cm"},
        "scale": {"dataType": "Numerical", "validValues": {"min": "0", "max": "300"}},
    }]
    response = await client.post("/brapi/v2/variables", json=payload)
    assert response.status_code == 200
    data = response.json()["result"]["data"]
    assert len(data) == 1
    var = data[0]
    assert var["observationVariableDbId"] is not None
    assert var["observationVariableName"] == "Plant Height"
    assert var["trait"]["traitName"] == "Plant Height"
    assert var["scale"]["dataType"] == "Numerical"


@pytest.mark.asyncio
async def test_post_variables_with_explicit_id(client, db_session):
    from brapi_light.models.core import Program, Study, Trial

    p = Program(program_db_id="p1", program_name="Wheat")
    t = Trial(trial_db_id="t1", trial_name="T1", program_db_id="p1")
    s = Study(study_db_id="s1", study_name="S1", program_db_id="p1", trial_db_id="t1")
    db_session.add_all([p, t, s])
    await db_session.commit()

    payload = [{
        "observationVariableDbId": "custom_v1",
        "observationVariableName": "Grain Yield",
        "studyDbId": "s1",
        "trait": {"traitName": "Grain Yield"},
        "scale": {"dataType": "Numerical"},
    }]
    response = await client.post("/brapi/v2/variables", json=payload)
    assert response.status_code == 200
    var = response.json()["result"]["data"][0]
    assert var["observationVariableDbId"] == "custom_v1"


@pytest.mark.asyncio
async def test_post_variables_upsert_existing(client, db_session):
    from brapi_light.models.core import Program, Study, Trial

    p = Program(program_db_id="p1", program_name="Wheat")
    t = Trial(trial_db_id="t1", trial_name="T1", program_db_id="p1")
    s = Study(study_db_id="s1", study_name="S1", program_db_id="p1", trial_db_id="t1")
    db_session.add_all([p, t, s])
    await db_session.commit()

    payload = [{
        "observationVariableDbId": "v_upsert",
        "observationVariableName": "Old Name",
        "trait": {"traitName": "Old Name"},
        "scale": {"dataType": "Text"},
    }]
    await client.post("/brapi/v2/variables", json=payload)

    payload2 = [{
        "observationVariableDbId": "v_upsert",
        "observationVariableName": "New Name",
        "trait": {"traitName": "New Name"},
        "scale": {"dataType": "Numerical"},
    }]
    resp = await client.post("/brapi/v2/variables", json=payload2)
    assert resp.status_code == 200
    var = resp.json()["result"]["data"][0]
    assert var["observationVariableName"] == "New Name"
    assert var["scale"]["dataType"] == "Numerical"

    # Verify only one variable with this ID exists
    get_resp = await client.get("/brapi/v2/variables")
    matching = [v for v in get_resp.json()["result"]["data"]
                if v["observationVariableDbId"] == "v_upsert"]
    assert len(matching) == 1


@pytest.mark.asyncio
async def test_post_variables_auto_generates_id(client, db_session):
    from brapi_light.models.core import Program, Study, Trial

    p = Program(program_db_id="p1", program_name="Wheat")
    t = Trial(trial_db_id="t1", trial_name="T1", program_db_id="p1")
    s = Study(study_db_id="s1", study_name="S1", program_db_id="p1", trial_db_id="t1")
    db_session.add_all([p, t, s])
    await db_session.commit()

    payload = [{
        "observationVariableName": "Auto ID Trait",
        "trait": {"traitName": "Auto ID Trait"},
        "scale": {"dataType": "Boolean"},
    }]
    response = await client.post("/brapi/v2/variables", json=payload)
    assert response.status_code == 200
    var = response.json()["result"]["data"][0]
    assert var["observationVariableDbId"] is not None
    assert len(var["observationVariableDbId"]) > 0
    assert var["observationVariableDbId"] != "custom_v1"  # not from another test
