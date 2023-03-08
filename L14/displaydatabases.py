import sqlite3
import pandas as pd
from IPython.display import display
from ipywidgets.widgets import Box,VBox,HBox,Output,Dropdown,Layout
class Display:
    def __init__(self):
        self.currentConnection = None
        self.currentDB = ''
        self.tableOut = Output(layout = Layout(max_width='30%'))
        self.schemaOut = Output()
        self.tableSelect = Dropdown(
            options=[''],
            value='',
            description='Table:',
            disabled=False,
        )
        self.databaseSelect = Dropdown(
            options=['sqlite-sakila','chinook'],
            value='sqlite-sakila',
            description='Database:',
            disabled=False,

        )
        self.tableSelect.observe(self.tableChange, names='value')
        self.databaseSelect.observe(self.databaseChange, names='value')
        self.displayDatabases = VBox([HBox([self.tableOut,VBox([self.databaseSelect,self.tableSelect])]),self.schemaOut])
        self.changeDatabase()
        
    @property
    def displayDatabases(self):
        return self._displayDatabases
    
    @displayDatabases.setter
    def displayDatabases(self, value):
        self._displayDatabases = value
    
    def changeDatabase(self):
        selectedDatabase = self.databaseSelect.value
        if self.currentConnection is None or self.currentDB != selectedDatabase:
            if self.currentConnection is not None:
                self.currentConnection.close()
            self.currentConnection = sqlite3.connect(f'databases/{selectedDatabase}.db')
            self.currentDB = f'{selectedDatabase}'
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';",self.currentConnection) 
        self.tableSelect.options = tables.name.values
        self.tableSelect.value = tables.name.values[0]

    def displayTable(self):
        query = f"select * from {self.tableSelect.value} limit 5"
        query2 = f"pragma table_info('{self.tableSelect.value}');"
        data = pd.read_sql_query(query,self.currentConnection)
        data2 = pd.read_sql_query(query2,self.currentConnection)[['name','type','pk']]
        self.tableOut.clear_output()
        self.schemaOut.clear_output()
        with self.tableOut:
            display(data)
        with self.schemaOut:
            display(data2)
        
    def tableChange(self,change):
        self.displayTable()

    def databaseChange(self,change):
        self.changeDatabase()