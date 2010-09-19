import constants as const
import sqlite3


class SQLite:
    def __init__(self):
        self.db = sqlite3.connect(const.SQLITE_DB)
        self.cursor = self.db.cursor()
        
        self.cursor.execute("""
            create table if not exists settings
            (id integer, server text, player text)
        """)
        self.db.commit()
        self.cursor.execute("""
            select * from settings
        """)
        if not self.cursor.fetchall():
            v_id = 1
            v_server = ''
            v_player = len(const.PLAYERS.keys()) > 0 and const.PLAYERS.keys()[0] or ''
            self.cursor.execute("""
                insert into settings (id, server, player)
                values (?, ?, ?)
            """, (v_id, v_server, v_player))
            self.db.commit()
    
    def SetServer(self, server):
        self.SetField('server', server)
    
    def GetServer(self):
        return self.GetField('server')
    
    def SetPlayer(self, player):
        self.SetField('player', player)
    
    def GetPlayer(self):
        return self.GetField('player')
    
    def SetField(self, field, value):
        self.cursor.execute("""
            update settings
            set %s = ?
            where id = 1
        """ % field, (value,))
        self.db.commit()
    
    def GetField(self, field):
        self.cursor.execute("""
            select %s
            from settings
            where id = 1
        """ % field)
        row = self.cursor.fetchone()
        if len(row) > 0:
            return row[0]
        else:
            return ""
