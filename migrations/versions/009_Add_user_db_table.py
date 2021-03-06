from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    """Add the users table we'll use """
    meta = MetaData(migrate_engine)
    user = Table('users', meta,
        Column('id', Integer, autoincrement=True, primary_key=True),
        Column('username', Unicode(255), unique=True),
        Column('password', Unicode(60)),
        Column('email', Unicode(255), unique=True),
        Column('activated', Boolean, server_default="0"),
        Column('is_admin', Boolean, server_default="0"),
        Column('last_login', DateTime),
    )

    user.create()

    # adding an initial user account with user/pass combo of admin:admin
    migrate_engine.execute(user.insert().values(username=u'admin',
                                                password=u'$2a$10$LoSEVbN6833RtwbGQlMhJOROgkjHNH4gjmzkLrIxOX1xLXNvaKFyW',
                                                email=u'testing@dummy.com',
                                                activated=True,
                                                is_admin=True))

def downgrade(migrate_engine):
    """And the big drop"""
    meta = MetaData(migrate_engine)
    user = Table('users', meta)
    user.drop()
