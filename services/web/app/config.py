import os


BASEDIR = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-Make-a-good-guess'
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = f"{os.getenv('BASEDIR')}/app/static"
    MEDIA_FOLDER = f"{os.getenv('BASEDIR')}/app/media"
    
    if os.getenv('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASEDIR, 'ModelAgency.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI',
                                        default=f"sqlite:///{os.path.join(BASEDIR, 'instance', 'test.db')}")
    WTF_CSRF_ENABLED = False
