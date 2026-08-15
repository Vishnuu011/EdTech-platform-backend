from src.config.settings import settings

print(f"APP_NAME: {settings.APP_NAME}")
print(f"APP_ENV: {settings.APP_ENV}")
print(f"DEBUG: {settings.DEBUG}")
print(f"APP_VERSION: {settings.APP_VERSION}")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"REDIS_URL: {settings.REDIS_URL}")
print(f"RABBITMQ_URL: {settings.RABBITMQ_URL}")
print(f"JWT_SECRET: {settings.JWT_SECRET}")
print(f"JWT_ALGORITHM: {settings.JWT_ALGORITHM}")