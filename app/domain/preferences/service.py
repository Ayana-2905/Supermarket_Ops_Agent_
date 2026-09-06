from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import Preference


class PreferenceService:

    def __init__(self, db: Session):
        self.db = db

    def set_preference(self, key: str, value: str):

        key = key.strip()
        value = value.strip()

        if not key or not value:
            raise ValueError(
                "PREFERENCE_KEY_AND_VALUE_REQUIRED"
            )

        preference = self.db.scalar(
            select(Preference).where(
                Preference.key == key
            )
        )

        if preference:
            preference.value = value
        else:
            preference = Preference(
                key=key,
                value=value
            )
            self.db.add(preference)

        self.db.commit()
        self.db.refresh(preference)

        return {
            "key": preference.key,
            "value": preference.value
        }

    def get_preference(self, key: str):

        preference = self.db.scalar(
            select(Preference).where(
                Preference.key == key
            )
        )

        if not preference:
            return None

        return preference.value

    def get_all_preferences(self):

        preferences = self.db.scalars(
            select(Preference)
        ).all()

        return {
            preference.key: preference.value
            for preference in preferences
        }