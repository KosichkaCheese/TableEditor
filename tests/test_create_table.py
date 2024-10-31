import pytest
from db import Database


@pytest.fixture
def db_instance():
    instance = Database("localhost", 5433, "test_db", "test", "test") # тестовая база данных

    # Подключаемся к тестовой базе данных
    instance.connect()
    # Очищаем базу перед каждым тестом
    yield instance
    
    if instance.connection:
        instance.cursor.close()
        instance.connection.close()


def test_create_table_no_columns(db_instance): #тест создания таблицы без столбцов
    table_name = "new_table"
    columns = []
    
    db_instance.cursor.execute("DROP TABLE IF EXISTS new_table CASCADE")
    db_instance.connection.commit()
    
    result = db_instance.create_table(table_name, columns)
    assert result is True
    
    
def test_create_table_with_columns(db_instance): #тест создания таблицы со столбцами
    table_name = "new_table"
    columns = [{"name": "column1", "orig_name": "column1", "type": "INT", "p_key": False},
               {"name": "column2", "orig_name": "column2", "type": "TEXT", "p_key": False}]
    
    db_instance.cursor.execute("DROP TABLE IF EXISTS new_table CASCADE")
    db_instance.connection.commit()
   
    result = db_instance.create_table(table_name, columns)
    assert result is True
    
    
def test_create_table_with_pk(db_instance): #тест создания таблицы с первичным ключем
    table_name = "new_table"
    columns = [{"name": "column1", "orig_name": "column1", "type": "INT", "p_key": True},
               {"name": "column2", "orig_name": "column2", "type": "TEXT", "p_key": False}]
    
    db_instance.cursor.execute("DROP TABLE IF EXISTS new_table CASCADE")
    db_instance.connection.commit()

    result = db_instance.create_table(table_name, columns)
    assert result is True
    