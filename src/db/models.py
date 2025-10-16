from datetime import UTC, datetime

import peewee
from peewee import Model, SqliteDatabase

from src.settings import BASE_DIR

# SQLite may not be suited for production, but is
# perfectly for the initial development phase
db = SqliteDatabase(BASE_DIR / "db.sqlite3")


class DbBaseModel(Model):
    created_at = peewee.DateTimeField(default=datetime.now(tz=UTC))
    updated_at = peewee.DateTimeField()

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(tz=UTC)
        return super().save(*args, **kwargs)

    class Meta:
        database = db


class User(DbBaseModel):
    discord_id = peewee.IntegerField(primary_key=True)
    sith_id = peewee.IntegerField(null=True)
    username = peewee.CharField()


class Club(DbBaseModel):
    name = peewee.CharField(max_length=64, unique=True)
    category_id = peewee.IntegerField(unique=True)
    sith_id = peewee.IntegerField(unique=True)
    president_role_id = peewee.IntegerField(unique=True)
    treasurer_role_id = peewee.IntegerField(unique=True)
    member_role_id = peewee.IntegerField(unique=True)
    former_member_role_id = peewee.IntegerField(unique=True)
    message_autorole_id = peewee.IntegerField(unique=True)


def init():
    db.create_tables([User, Club])
