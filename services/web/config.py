import os
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-Make-a-good-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or \
        'sqlite:///' + os.path.join(BASEDIR, 'ModelAgency.db')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    POSTS_PER_PAGE = 25
    DEVELOPMENT = True
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or 'your-google-client-id'
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or 'your-google-client-secret'
    
    DATABASE_URL='postgres+postgresql://ModelAgency:ModelAgency@db:5432/ModelAgency'
    
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STATIC_FOLDER = f"{os.environ.get('BASEDIR')}/app/static"
    MEDIA_FOLDER = f"{os.environ.get('BASEDIR')}/app/media"
    UPLOAD_FOLDER = f"{os.environ.get('APP_FOLDER')}/app/upload"
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


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
