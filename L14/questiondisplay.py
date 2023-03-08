import sqlite3
import pandas as pd
from IPython.display import display,HTML
from ipywidgets.widgets import VBox,HBox,Output,Layout,Textarea,Button
import databases

class QueryWindow: 
    def __init__(self,qNo):
        self.qNo = qNo
        self.qOut = Output()
        self.queryArea = Textarea(
            value='',
            placeholder='Type your Query here',
            description='',
            disabled=False,
            #layout = Layout(max_width='30%')
        )
        self.execute = Button(
            description='Execute',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
            tooltip='Execute',
            #layout = Layout(max_width='20%')
        )
        self.resultMessage = Output()
        self.execute.on_click(self.executeQuery)
        self.yourOutput = Output(layout = Layout())
        self.expectedOutput = Output(layout = Layout())
        self.yourOut = Output()
        self.expectOut = Output()
        with self.yourOut:
            display(HTML('<b>Your Ouput:</b>'))
        with self.expectOut:
            display(HTML('<b>Expected Ouput:</b>'))
        self.disPlayWindow = VBox([HBox([self.qOut,self.queryArea,self.execute,self.resultMessage]),\
        VBox([VBox([self.expectOut,self.expectedOutput]\
                   ),VBox([self.yourOut,self.yourOutput])])]\
                                  ,layout = Layout(width='80%'))
        self.qset = pd.read_csv('questions.csv')
        self.questionData = self.qset.loc[self.qset.qNo==self.qNo]
        expected = self.getExpected()
        with self.expectedOutput:
            display(expected)  
        with self.qOut:
            print (self.questionData.question.values[0])
            
    def getExpected(self):
        expected = pd.read_pickle('results/'+self.questionData.results.values[0])
        if self.questionData.result_type.values[0] != 'set':
            expected = expected.iloc[0][0]
        return expected
    
    def display(self):
        return self.disPlayWindow
    
    def executeQuery(self,event):
        self.resultMessage.clear_output()
        self.yourOutput.clear_output()
        db = databases.getDB(self.questionData.database.values[0])
        error = False
        try:
            result  = pd.read_sql_query(self.queryArea.value,db)
        except:
            with self.resultMessage:
                display(HTML('<span style="color:red">Error in processing your query. Please check syntax and retry</span>'))
            error = True
        if not error:
            match=False
            expected = self.getExpected()
            if self.questionData.result_type.values[0] != 'set':
                if result.shape == (1,1):
                    result = result.iloc[0][0]
                    match = result == expected
            else:
                if not self.questionData.isOrder.values[0]:
                    #check all columns are same
                    if set(result.columns.values)==set(expected.columns.values):
                        match=result.sort_values(by=[self.questionData.sort_key.values[0]])\
                        .reset_index(drop=True).equals(expected.sort_values(by=[self.questionData.sort_key.values[0]])\
                                                       .reset_index(drop=True))
                else:
                    match = result.reset_index(drop=True).equals(expected.reset_index(drop=True))
            with self.yourOutput:
                display(result)
            msg = '<span style="color:green">Success!!!!!</span>'
            if not match:
                msg = '<span style="color:red">Sorry your query results doesnot match the expected result. Please try again</span>'
            with self.resultMessage:
                display(HTML(msg))