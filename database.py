import sqlite3
import logging
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name):
        self.db = db_name
        self.create_table()
    
    def create_table(self):
        """Veritabanı tablolarını oluşturur veya kontrol eder."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()

            sql_query_1 = """
            CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            cases INTEGER DEFAULT 0
            )"""

            sql_query_2 = """
            CREATE TABLE IF NOT EXISTS items(
            item_name TEXT PRIMARY KEY, 
            item_price INTEGER,
            item_description TEXT
            )"""

            sql_query_3 = """
            CREATE TABLE IF NOT EXISTS items_users(
            user_id TEXT,
            item_name TEXT,
            item_count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, item_name), -- <--- YENİ: Bir kullanıcının envanterinde bir eşyadan sadece 1 satır olabilir
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(item_name) REFERENCES items(item_name)
            )"""

            cursor.execute(sql_query_1)
            cursor.execute(sql_query_2)
            cursor.execute(sql_query_3)
            con.commit()

    def get_balance(self, user_id: str):
        """Kullanıcının bakiyesini alır. Kullanıcı yoksa oluşturur."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row is None:
                cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
                con.commit()
                return 0
            
            return row[0]

    def update_balance(self, user_id: str, amount: int):
        """Kullanıcının bakiyesine miktar ekler/çıkarır (tek işlemde)."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
            
            current_balance = self.get_balance(user_id)
            
            new_balance = current_balance + amount
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            con.commit()
            
            return new_balance
    
    def get_cases(self, user_id: str):
        """Kullanıcının kasa sayısını alır. Kullanıcı yoksa oluşturur."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
            
            cursor.execute("SELECT cases FROM users WHERE user_id = ?", (user_id,)) 
            row = cursor.fetchone()
            
            if row is None:
                cursor.execute("INSERT INTO users (user_id, balance, cases) VALUES (?, ?, ?)", (user_id, 0, 0))
                con.commit()
                return 0
            
            return row[0]

    def update_cases(self, user_id: str, amount: int):
        """Kullanıcının kasa sayısına ekler/çıkarır (tek işlemde)."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()

            current_count = self.get_cases(user_id)

            new_count = current_count + amount
            cursor.execute("UPDATE users SET cases = ? WHERE user_id = ?", (new_count, user_id))
            con.commit()
            
            return new_count

    def get_item_count(self, user_id: str, item_name: str):
        """Bir kullanıcının belirli bir eşyadan kaç tane olduğunu alır."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
            cursor.execute("SELECT item_count FROM items_users WHERE user_id = ? AND item_name = ?", (user_id, item_name))
            row = cursor.fetchone()
            
            if row is None:
                cursor.execute("INSERT INTO items_users (user_id, item_name, item_count) VALUES (?, ?, ?)", (user_id, item_name, 0))
                con.commit()
                return 0

            return row[0]
    
    def update_item_count(self, user_id: str, item_name: str, amount: int):
        """Kullanıcının eşya sayısını günceller (tek işlemde)."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()

            current_count = self.get_item_count(user_id, item_name)
            new_count = current_count + amount

            cursor.execute("UPDATE items_users SET item_count = ? WHERE user_id = ? AND item_name = ?", (new_count, user_id, item_name))
            con.commit()

            return new_count
    
    def get_item_price(self, item_name: str):
        """Eşyanın fiyatını alır."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
            cursor.execute("SELECT item_price FROM items WHERE item_name = ?", (item_name,))
            row = cursor.fetchone()
            
            return row[0] if row else None
    
    def get_user_inventory(self, user_id: str):
        """Kullanıcının envanterini bir sözlük (dict) olarak döner."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()

            cursor.execute("SELECT item_name, item_count FROM items_users WHERE user_id = ? AND item_count > 0", (user_id,))
            rows = cursor.fetchall()

            if not rows:
                return {}
            
            return {item_name: count for item_name, count in rows}

    def get_all_items(self):
        """Marketteki tüm eşyaları bir sözlük (dict) olarak döner."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
            cursor.execute("SELECT item_name, item_price, item_description FROM items")
            rows = cursor.fetchall()
            
            if not rows:
                return {}

            return {name: {'price': price, 'description': desc} for name, price, desc in rows}

    def add_item(self, item_name: str, item_price: int, description: str):
        """Markete yeni bir eşya ekler."""
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()

            cursor.execute("INSERT OR IGNORE INTO items (item_name, item_price, item_description) VALUES (?, ?, ?)", 
                           (item_name, item_price, description))
            con.commit()

if __name__ == "__main__":
    db = Database("users.db")
    
    logger.info("Veritabanı tabloları oluşturuluyor/kontrol ediliyor...")
    db.create_table()
    logger.info("Tablolar hazır.")
    
    
    logger.info("Market eşyaları ekleniyor (varsa geçilecek)...")
    db.add_item("Hacı'nın Aleti", 50000, "Koleksiyon eşyası.")
    db.add_item("Benim Adım Cafer", 75000, "Koleksiyon eşyası.")
    db.add_item("Umidi Zı Babo Men", 100000, "Günlük ödülünüzü 9000 🪙 ve 3 kasaya çıkarır.")
    db.add_item("Burak Yılmaz", 80000, "Koleksiyon eşyası.")
    db.add_item("İbo'nun Steteskopu", 4500000, "Koleksiyon eşyası.")

    db.update_balance("763792915742720041",500000)
    db.update_balance("317318237018914826",500000)
    db.update_balance("840325381935333396",500000)
    db.update_balance("817041365066055701",500000)
    db.update_balance("699136507893645413",500000)
    db.update_balance("782595820628738058",500000)

    logger.info("Market eşyaları eklendi.")
    
    logger.info("\n--- Test: Market içeriği ---")
    market_items = db.get_all_items()
    for item, details in market_items.items():
        logger.info(f"- {item} ({details['price']} coin): {details['description']}")