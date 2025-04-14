#!/bin/bash

echo "📦 Применяем миграции..."
alembic upgrade head

echo "🚀 Запускаем FastAPI..."
exec "$@"
