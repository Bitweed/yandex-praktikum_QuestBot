import sqlite3


class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_file)
        self.create_tables()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        """Создадим таблицу, если её нет."""

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                has_key INTEGER,
                step INTEGER
            );
        """)
        self.conn.commit()

    def save_user_data(self, user_id, has_key, step):
        """Сохранение данных пользователя."""

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, has_key, step)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            has_key = excluded.has_key,
            step = excluded.step;
        """, (user_id, has_key, step))
        self.conn.commit()

    def get_user_data(self, user_id):
        """Получение данных."""

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

    def set_user_step(self, user_id, step):
        """Установка значения шага для пользователя."""

        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET step = ? WHERE user_id = ?", (step, user_id))
        self.conn.commit()
