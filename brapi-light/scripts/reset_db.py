"""重置 brapi-light 数据库到初始 demo 状态。"""

import json
import sys
from pathlib import Path

# Ensure brapi-light is on sys.path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brapi_light.database.base import Base
from brapi_light.database.engine import async_session_factory, engine
from brapi_light.models.core import Location, Person, Program, Season, Study, Trial
from brapi_light.models.phenotyping import ObservationUnit, ObservationVariable


async def reset():
    # Drop and recreate all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        p = Program(program_db_id="p1", program_name="Wheat Breeding 2026")
        t = Trial(trial_db_id="t1", trial_name="Drought Tolerance", program_db_id="p1")
        s = Study(
            study_db_id="s1", study_name="Field A", common_crop_name="Wheat",
            location_name="Test", active=True, program_db_id="p1", trial_db_id="t1",
        )
        loc = Location(location_db_id="l1", location_name="Test Field")
        season = Season(season_db_id="season1", season="2026", year="2026")
        person = Person(person_db_id="person1", first_name="Jane", last_name="Doe",
                        email="janedoe@test.local")
        db.add_all([p, t, s, loc, season, person])
        await db.flush()

        variables = [
            ObservationVariable(
                observation_variable_db_id="v1",
                observation_variable_name="Plant Height",
                study_db_id="s1",
                trait=json.dumps({
                    "traitDbId": "t1", "traitName": "Plant Height",
                    "traitDescription": "Plant height measured in cm",
                }),
                scale=json.dumps({
                    "dataType": "Numerical",
                    "validValues": {"minimumValue": "0", "maximumValue": "300"},
                }),
            ),
            ObservationVariable(
                observation_variable_db_id="v2",
                observation_variable_name="Grain Yield",
                study_db_id="s1",
                trait=json.dumps({
                    "traitDbId": "t2", "traitName": "Grain Yield",
                    "traitDescription": "Grain yield in kg/ha",
                }),
                scale=json.dumps({
                    "dataType": "Numerical",
                    "validValues": {"minimumValue": "0", "maximumValue": "10000"},
                }),
            ),
            ObservationVariable(
                observation_variable_db_id="v3",
                observation_variable_name="Leaf Color",
                study_db_id="s1",
                trait=json.dumps({
                    "traitDbId": "t3", "traitName": "Leaf Color",
                    "traitDescription": "Leaf color assessment",
                }),
                scale=json.dumps({
                    "dataType": "Categorical",
                    "validValues": {
                        "categories": [
                            {"value": "Green"},
                            {"value": "Yellow"},
                            {"value": "Brown"},
                        ],
                    },
                }),
            ),
        ]
        db.add_all(variables)
        await db.flush()

        units = []
        for i in range(1, 4):
            units.append(ObservationUnit(
                observation_unit_db_id=f"plot{i}",
                observation_unit_name=f"Plot {i}",
                study_db_id="s1",
                germplasm_db_id=f"g{i}",
                germplasm_name=f"Wheat Line {i}",
                observation_unit_position=json.dumps({
                    "entryType": "TEST",
                    "geoCoordinates": {},
                    "observationLevel": {"levelName": "plot", "levelOrder": 1},
                    "positionCoordinateX": str(i),
                    "positionCoordinateXType": "GRID_COL",
                }),
            ))
        db.add_all(units)
        await db.commit()

    print("数据库已重置 — 3 variables, 3 observation units")


if __name__ == "__main__":
    import asyncio
    asyncio.run(reset())
