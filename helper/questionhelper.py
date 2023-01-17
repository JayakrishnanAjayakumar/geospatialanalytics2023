import ipywidgets as widgets
import os
import functools
import json
from collections import OrderedDict
from IPython.display import display,clear_output
import jsonpickle
import pandas as pd
import requests
import shutil
import tempfile
import markdown
class Question:
    def __init__(self,qid):
        self.qid = qid
        self.marks = None
        self.qText = None
        self.qType = None
        self.qImageDetails = None
        self.results = {'options':None,'choice':None}
    
    def on_value_change(self,val):
        #if its a file then do something else
        if self.qType == '5':
            #upload the file to the system one by one
            out = []
            files = val['new']
            for fil in files:
                res = fil.copy()
                res.pop('content', None)
                out.append(res)
                if not os.path.isdir('uploads'):
                    os.mkdir('uploads')
                #now download the content to the location
                with open('uploads\\'+fil['name'], "wb") as fp:
                    fp.write(fil['content'])
            self.results['choice'] = tuple(out)
        else:
            self.results['choice'] = val['new']
        
    def clearFiles(self,fileWidget,_):
        fileWidget.value=()
        self.results['choice'] = ()
        #fileWidget._counter=0 

    def view(self):
        out = []
        out.append(widgets.HTML(
            value=markdown.markdown(self.qText,extensions=['fenced_code'])+f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(<b>{self.marks}</b>)",
            placeholder='',
            description='',
        ))
        if self.qImageDetails is not None:
            out.append(widgets.Image(
                value=open('images/'+self.qImageDetails['name'],'rb').read(),
                format=os.path.splitext(self.qImageDetails['name'])[1],
                width=720,
                height=450,
            ))
        widg=None
        #Single choice question
        if self.qType=='1':
            widg = widgets.RadioButtons(
                options=self.results['options'],
                description='',
                value = self.results['choice'],
                disabled=False
            )
        #Multiple choice question
        if self.qType=='2': 
            widg = widgets.SelectMultiple(
                options=self.results['options'],
                value=[] if self.results['choice'] is None else self.results['choice'],
                rows=5,
                description='',
                disabled=False)
        #Text box answer
        elif self.qType == '3':
            #text box answers
            widg = widgets.Text(
                value=self.results['choice'],
                placeholder='',
                description='',
                disabled=False
            )
        elif self.qType in ['4','6']:
            #code block and text block answers
            widg = widgets.Textarea(layout={'width': '50%','height':'200px'},value=self.results['choice'],disabled=False)
        elif self.qType == '5':
            #file uploads, check first whether a file was previously uploaded
            existing = []
            if self.results['choice'] is not None:
                for fil in self.results['choice']:
                    fcopy = fil.copy()
                    if os.path.exists('uploads\\'+fcopy['name']):
                        fcopy['content'] = memoryview(open('uploads\\'+fil['name'],'rb').read())
                        existing.append(fcopy)
            existing = tuple(existing)
            self.results['choice'] = existing
            fileWidg = widgets.FileUpload(
                value=existing,
                accept='',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
                multiple=True  # True to accept multiple files upload else False
            )
            fileWidg.observe(self.on_value_change, names='value')
            clearbutton = widgets.Button(
                description='Clear',
                disabled=False,
                button_style='info'
            )
            clearbutton.on_click(functools.partial(self.clearFiles, fileWidg))
            widg = widgets.HBox([fileWidg,clearbutton])
        if self.qType != '5':
            widg.observe(self.on_value_change, names='value')
        out.append(widg)
        return widgets.VBox(out)
    
class QuestionSet:
    def __init__(self):
        self.uid = None
        self.totalMarks = None
        self.questions = OrderedDict()
        self.qKeys = None
        #read the questionset json and create the questionset
        self.parseQuestionSet()
        
    def setQuestion(self,qObj):
        self.questions[qObj.qid] = qObj
        
    def showErrors(self,errorWidget,val):
        #loop through each question
        error = []
        noRespError = 'No response provided'
        for idx,qObj in enumerate(self.questions.values()):
            qType = qObj.qType
            if qObj.results['choice'] is None:
                error.append([idx+1,noRespError])
                continue
            if qType == '2':
                if len(qObj.results['choice'])==0:
                    error.append([idx+1,noRespError])
            elif qType in ['3','4','6']:
                if len(qObj.results['choice'].strip())==0:
                    error.append([idx+1,noRespError])
            elif qType == '5':
                if len(qObj.results['choice'])==0:
                    error.append([idx+1,noRespError])
                #loop through each files and check if it exsists
                else:
                    missingFiles = []
                    for fil in qObj.results['choice']:
                        if not os.path.isfile(f'uploads\\{fil["name"]}'):
                            missingFiles.append(fil["name"])
                    if len(missingFiles)>0:
                        error.append([idx+1,'Files '+",".join(missingFiles)+' are missing from the upload folder.'])
        with errorWidget:
            clear_output()
            if len(error)>0:
                display(pd.DataFrame(error,columns=['Question','Error']))
            else:
                print ('No errors')
    
    def submitQuestionSet(self,nameWidget,pwdWidget,errorWidget,_):
        error = 'Succesfully Submitted'
        if (not nameWidget.value) or (not pwdWidget.value):
            error = 'User name and password are mandatory'
        else:
            #send this to server
            #first create a zip with the current directory name
            dirname = os.path.basename(os.getcwd())
            with tempfile.TemporaryDirectory() as tmpdirname:
                shutil.make_archive(tmpdirname+'/'+dirname,'xztar')
                shutil.copy(tmpdirname+'/'+dirname+'.tar.xz', dirname+'.tar.xz')
            response = None
            with open(dirname+'.tar.xz','rb') as fil:
                files = {'answerdata': fil}
                response = requests.post('https://ghhlab.epbi.cwru.edu/Geospatial2023/submitExam',data={'uname':nameWidget.value,'password':pwdWidget.value,'fname':dirname+'.tar.xz'},files=files,verify=False)
            if not response.status_code == 200:
                error = 'Not able to connect to the server'
            else:
                result = response.json()
                if 'Error' in result:
                    error = result['Error']
            os.remove(dirname+'.tar.xz')
        with errorWidget:
            clear_output()
            print (error)
        
            
    def showSubmitSection(self):
        showerrorbutton = widgets.Button(
                description='Show Errors',
                disabled=False,
                button_style='danger'
        )
        submitbutton = widgets.Button(
                description='Submit',
                disabled=False,
                button_style='success'
        )
        savebutton = widgets.Button(
                description='Save',
                disabled=False,
                button_style='info'
        )
        uname = widgets.Text(
                value='',
                placeholder='',
                description='User',
                disabled=False
        )
        password = widgets.Password(
                value='',
                placeholder='',
                description='Password:',
                disabled=False
        )
        totMarks = widgets.HTML(
            value=markdown.markdown(f"Total Marks:<b>{self.totalMarks}</b>"),
            placeholder='',
            description='',
        )
        errorDisplay = widgets.Output(layout={'border': '1px solid black'})
        savebutton.on_click(self.saveQuestionSet)
        submitbutton.on_click(functools.partial(self.submitQuestionSet,uname,password,errorDisplay))
        showerrorbutton.on_click(functools.partial(self.showErrors, errorDisplay))
        display(widgets.VBox([widgets.HBox([savebutton,showerrorbutton,submitbutton,uname,password,totMarks]),errorDisplay]))
        
    def saveQuestionSet(self,val):
        out = {'uid':self.uid,'total':self.totalMarks,'questions':[]}
        for qid in self.questions:
            out['questions'].append(jsonpickle.encode(self.questions[qid]))
        with open(r'question_set.json','w') as outFile:
            outFile.write(json.dumps(out))
            
    def getQuestion(self,qNo):
        qid = self.qKeys[qNo-1]
        qObj = self.questions[qid]
        qView = qObj.view()
        savebutton = widgets.Button(
                description='Save',
                disabled=False,
                button_style='success'
        )
        savebutton.on_click(self.saveQuestionSet)
        return display(widgets.VBox([qView,savebutton]))
    
    def parseQuestionSet(self,filepath='question_set.json'):
        if os.path.isfile(filepath):
            questionData = json.loads(open(filepath).read())
            self.uid = questionData['uid']
            self.totalMarks = questionData['total']
            #now iterate through each question and create question objects
            for question in questionData['questions']:
                qObj = jsonpickle.decode(question)
                self.questions[qObj.qid] = qObj
            self.qKeys = list(self.questions.keys())