import pytest
from db import Database


@pytest.fixture
def db_instance():
    instance = Database("localhost", 5433, "test_db", "test", "test") #тестовая база данных

    # Подключаемся к тестовой базе данных
    instance.connect()
    
    # Очищаем базу перед каждым тестом
    yield instance
    
    # Закрываем подключение после теста
    if instance.connection:
        instance.cursor.close()
        instance.connection.close()


def test_edit_table_rename(db_instance): #тест переименования таблицы
    #входные параметры
    table_name = "old_table"
    new_table_name = "new_table"
    columns = [
        {"name": "column1", "orig_name": "column1", "type": "INT", "p_key": False}
    ]
    
    #если есть таблицы, удаляем
    db_instance.cursor.execute("DROP TABLE IF EXISTS old_table CASCADE")
    db_instance.cursor.execute("DROP TABLE IF EXISTS new_table CASCADE")
    db_instance.connection.commit()
    #создаем таблицу заново
    db_instance.cursor.execute("CREATE TABLE IF NOT EXISTS old_table (column1 INT)")
    db_instance.connection.commit()
    #получаем результат функции, проверяем, что он True
    result = db_instance.edit_table_content(table_name, new_table_name, columns)
    assert result is True


def test_edit_table_add_column(db_instance): #тест добавления столбца
    table_name = "old_table"
    new_table_name = "old_table"
    columns = [
        {"name": "column1", "orig_name": "column1", "type": "INT", "p_key": False},
        {"name": "column2", "orig_name": "column2", "type": "TEXT", "p_key": False}
    ]
    
    db_instance.cursor.execute("DROP TABLE IF EXISTS old_table CASCADE")
    db_instance.connection.commit()
    
    db_instance.cursor.execute("CREATE TABLE IF NOT EXISTS old_table (column1 INT)")
    db_instance.connection.commit()

    result = db_instance.edit_table_content(table_name, new_table_name, columns)
    assert result is True


def test_edit_table_modify_column_type(db_instance): #тест изменения типа столбца
    table_name = "old_table"
    new_table_name = "old_table"
    columns = [
        {"name": "column1", "orig_name": "column1", "type": "TEXT", "p_key": False}
    ]
    
    db_instance.cursor.execute("DROP TABLE IF EXISTS old_table CASCADE")
    db_instance.connection.commit()
    
    db_instance.cursor.execute("CREATE TABLE IF NOT EXISTS old_table (column1 INT)")
    db_instance.connection.commit()

    result = db_instance.edit_table_content(table_name, new_table_name, columns)
    assert result is True


def test_edit_table_remove_column(db_instance): #тест удаления столбца
    table_name = "old_table"
    new_table_name = "old_table"
    columns = [
    ]
    
    db_instance.cursor.execute("DROP TABLE IF EXISTS old_table CASCADE")
    db_instance.connection.commit()
    
    db_instance.cursor.execute("CREATE TABLE IF NOT EXISTS old_table (column1 INT)")
    db_instance.connection.commit()

    result = db_instance.edit_table_content(table_name, new_table_name, columns)
    assert result is True


def test_edit_table_change_primary_key_not_exist(db_instance): #тест добавления первичного ключа
    table_name = "old_table"
    new_table_name = "old_table"
    columns = [
        {"name": "column1", "orig_name": "column1", "type": "INT", "p_key": True}
    ]
    
    db_instance.cursor.execute("DROP TABLE IF EXISTS old_table CASCADE")
    db_instance.connection.commit()
    
    db_instance.cursor.execute("CREATE TABLE IF NOT EXISTS old_table (column1 INT)")
    db_instance.connection.commit()

    result = db_instance.edit_table_content(table_name, new_table_name, columns)
    assert result is True

def test_edit_table_change_primary_key_exist(db_instance): #тест изменения существующего первичного ключа
    table_name = "old_table"
    new_table_name = "old_table"
    columns = [{'name': 'aaaaaaaaa', 'orig_name': 'aaaaaaaaa', 'type': 'INT', 'p_key': True}, {'name': 'bbbbb', 'orig_name': 'bbbbb', 'type': 'TEXT', 'p_key': False}, {'name': 'cccccc', 'orig_name': 'cccccc', 'type': 'TEXT', 'p_key': False}, {'name': 'date', 'orig_name': 'date', 'type': 'TIMESTAMP', 'p_key': False}]
    
    db_instance.cursor.execute("DROP TABLE IF EXISTS old_table CASCADE")
    db_instance.connection.commit()
    
    db_instance.cursor.execute("CREATE TABLE IF NOT EXISTS old_table (aaaaaaaaa INT, bbbbb TEXT, cccccc TEXT, date TIMESTAMP, PRIMARY KEY (aaaaaaaaa, bbbbb))")
    db_instance.connection.commit()

    result = db_instance.edit_table_content(table_name, new_table_name, columns)
    assert result is True
