import psycopg
from psycopg import sql

class Database:
    def __init__(self, host, port, dbname, user, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.connection=None
    
    def connect(self):
        try:
            self.connection = psycopg.connect( #подключение с переданными параметрами
                host=self.host,
                port=self.port,
                dbname=self.dbname, 
                user=self.user, 
                password=self.password
            )
            self.cursor = self.connection.cursor() #задаем курсор
            return True
        except Exception as e: #в случае ошибки, возвращаем ее, чтобы вызвать уведомление
            return e
                
    def create_database(self): #метод создания базы данных с пользовательскими параметрами, используя существующую по умолчанию бд
        with psycopg.connect( #используем отдельное подключение
            host=self.host, 
            port=self.port,
            dbname="postgres",
            user=self.user, 
            password=self.password,  
            autocommit=True
        ) as connect:
            with connect.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.dbname)))
        return self.connect() #пытаемся подключиться к созданной базе
    
    def get_tables(self): #метод получения имён таблиц
        self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = self.cursor.fetchall()
        tables_name = [table[0] for table in tables]
        return tables_name
            
    def table_info(self, table_name): #получение информации о столбцах таблицы
            mapping = { #перевод типов данных в отображаемые в интерфейсе
                'integer': 'INT',
                'double precision': 'REAL',
                'real': 'REAL',
                'character varying': 'TEXT',
                'text': 'TEXT',
                'date': 'DATE',
                'timestamp without time zone': 'TIMESTAMP',
                'timestamp with time zone': 'TIMESTAMP'
            }
            self.cursor.execute(sql.SQL("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = {}").format(sql.Literal(table_name)))
            columns = self.cursor.fetchall()
            format_columns=[]
            
            for column in columns:
                item = (column[0],mapping.get(column[1], 'TEXT'))
                format_columns.append(item)
                
            return format_columns
    
    def table_constraint(self, table_name): #получение ограничений таблицы
        self.cursor.execute(sql.SQL("SELECT kcu.column_name FROM information_schema.key_column_usage AS kcu JOIN information_schema.table_constraints AS tc ON kcu.constraint_name = tc.constraint_name WHERE tc.table_name = {} AND tc.constraint_type = 'PRIMARY KEY'").format(sql.Literal(table_name)))
        constraint = self.cursor.fetchall()
        keys = [_[0] for _ in constraint]
        return keys
    
    def create_table(self, table_name, columns): #создание новой таблицы
        try:
            column_sql=[]
            p_keys_sql=[]
            
            for column in columns:
                #извлекаем параметры столбца
                name=column["name"]
                type=column["type"]
                p_key=column["p_key"]
                
                column_str = sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(type))
                column_sql.append(column_str)
                
                if p_key: #если указан первичный ключ, добавляем в выражение первичного ключа
                    p_keys_sql.append(sql.Identifier(name))
                
            if p_keys_sql:
                p_key_str = sql.SQL(", PRIMARY KEY ({})").format(sql.SQL(', ').join(p_keys_sql))
            else:
                p_key_str = sql.SQL("")
            
            #собираем выражение
            query = sql.SQL("CREATE TABLE {table_name} ({columns}{p_key_str})").format(
                table_name=sql.Identifier(table_name),
                columns=sql.SQL(', ').join(column_sql),
                p_key_str=p_key_str
            )
            with self.connection.cursor() as cursor:
                cursor.execute(query)
            self.connection.commit()
            return True
            
        except Exception as e:
            self.connection.rollback()
            return e
    
    def edit_table_content(self, table_name, new_table_name, columns): #изменение содержимого таблицы
        try:
            if new_table_name != table_name: #прверяем изменение имени
                cur_pkeys = self.table_constraint(table_name)
                #переименовываем таблицу
                query = sql.SQL("ALTER TABLE {table_name} RENAME TO {new_table_name}").format(
                    table_name=sql.Identifier(table_name),
                    new_table_name=sql.Identifier(new_table_name)
                )
                self.cursor.execute(query)
                #удаляем старые первичные ключи
                update_constraint = sql.SQL("ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}").format(
                    table=sql.Identifier(new_table_name),
                    constraint=sql.Identifier(table_name + '_pkey')
                )
                self.cursor.execute(update_constraint)
                if cur_pkeys: #добавляем новые первичные ключи с новым именем таблицы
                    new_constr = sql.SQL("ALTER TABLE {table} ADD CONSTRAINT {constraint} PRIMARY KEY ({columns})").format(
                        table=sql.Identifier(new_table_name),
                        constraint=sql.Identifier(new_table_name + '_pkey'),
                        columns=sql.SQL(', ').join([sql.Identifier(column) for column in cur_pkeys])
                    )
                    self.cursor.execute(new_constr)
                self.connection.commit()
                table_name = new_table_name #обновляем переменную имени таблицы
            
            cur_columns = dict(self.table_info(table_name)) #текущие столбцы
            cur_pkeys = self.table_constraint(table_name) #текущие первичные ключи
            new_pkeys = [column["name"] if column["name"] else column["orig_name"] for column in columns if column["p_key"]]
            
            for column in columns:
                name = column["name"]
                orig_name = column["orig_name"]
                type = column["type"]
            
                if orig_name in cur_columns and orig_name != name: #если изменилось имя столбца - меняем
                    self.cursor.execute(sql.SQL("ALTER TABLE {new_table_name} RENAME COLUMN {orig_name} TO {name}").format(
                        new_table_name=sql.Identifier(new_table_name),
                        orig_name=sql.Identifier(orig_name),
                        name=sql.Identifier(name)
                    ))
                    orig_name = name
                    cur_columns = dict(self.table_info(table_name))
                    
                if name not in cur_columns: #если добавлен новый столбец - добавляем
                    self.cursor.execute(sql.SQL("ALTER TABLE {new_table_name} ADD COLUMN {name} {type}").format(
                        new_table_name=sql.Identifier(new_table_name),
                        name=sql.Identifier(name),
                        type=sql.SQL(type)
                    ))
                elif type != cur_columns[name]: #если изменился тип существующего столбца - меняем тип
                    self.cursor.execute(sql.SQL("ALTER TABLE {new_table_name} ALTER COLUMN {name} TYPE {type}").format(
                        new_table_name=sql.Identifier(new_table_name),
                        name=sql.Identifier(name),
                        type=sql.SQL(type)
                    ))
            
            new_col_names = {column["name"] for column in columns}
            remove_cols = set(cur_columns.keys()) - new_col_names #сравниваем множества столбцов, чтобы понять, какие нужно удалить
            for col in remove_cols:
                self.cursor.execute(sql.SQL("ALTER TABLE {new_table_name} DROP COLUMN {col}").format(
                    new_table_name=sql.Identifier(new_table_name),
                    col=sql.Identifier(col)
                ))
            
            if cur_pkeys != new_pkeys: #если первичный ключ изменился
                if cur_pkeys: #удаляем существующий если есть
                    drop_constraint = sql.SQL("ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}").format(
                        table=sql.Identifier(new_table_name),
                        constraint=sql.Identifier(new_table_name + '_pkey')
                    )
                    self.cursor.execute(drop_constraint)
                    self.connection.commit()
                if new_pkeys: #добавляем новый если он есть
                    add_primary_key = sql.SQL("ALTER TABLE {table} ADD PRIMARY KEY ({columns})").format(
                        table=sql.Identifier(new_table_name),
                        columns=sql.SQL(', ').join(sql.Identifier(col) for col in new_pkeys)
                    )
                    self.cursor.execute(add_primary_key)
            
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            return e
            
    def delete_table(self, table_name): #удаление таблицы
        try:
            self.cursor.execute(sql.SQL("DROP TABLE {} CASCADE").format(sql.Identifier(table_name)))
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            return e    

    def close(self):
        self.cursor.close()
        self.connection.close()