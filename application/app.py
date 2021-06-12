# -*- coding: utf-8 -*-
"""
Created on Wed May 26 14:28:01 2021

@author: PRATHEEK
"""
from io import BytesIO
import sqlite3
from flask import(
    Flask,
    redirect,
    render_template,
    request,
    url_for,
    send_file
)
import json
import pandas as pd
import base64
import datetime
import spacy
from spacy import displacy
from wordcloud import wordcloud,STOPWORDS
nlp = spacy.load("medical_ner")
app=Flask(__name__)
app.secret_key='established 2021'
@app.route('/login',methods=['POST',    'GET'])
def login():
    if request.method=='POST':
        #session.pop('user_id',None)
        username=request.form['username']
        password=request.form['password']
        with sqlite3.connect("test.db") as db:
                     cursor=db.cursor()
                     find_user =("select * from users WHERE username=? AND password=?")
                     cursor.execute(find_user,[(username),(password)])
                     results=cursor.fetchall()  
        print(results)
        if results:    
            return redirect(url_for('profile'))
        else:
            return render_template('index.html',login_status=True)
        #return redirect(url_for('login'))
            
    return render_template('index.html',login_status=False)

@app.route('/profile')
def profile():
    return render_template('2nd page.html')
@app.route('/finalpage')
def finalpage():
    df = pd.read_csv(r"output.csv")
    colors = {"DRUG": "linear-gradient(90deg, #aa9cfc, #fc9ce7)","ADR":"linear-gradient(to right, #3486DA, #e5e5be)"}
    options = {"ents": ["DRUG","ADR"], "colors": colors}
        
    def displacy_func(x):
            html = displacy.render([nlp(x)],style="ent",jupyter=False,options=options)
            return html
        
    df['tableop'] = df['Sentence'].apply(displacy_func)
    
    return render_template('finalpage.html',data=list(df['tableop']))

def get_ner(df1):
    def get_adr(x):
        doc=nlp(x)
        entities=[]
        for ent in doc.ents:
            e=(ent.label_,ent.text)
            entities.append(e)
        return entities
    df1['NER']=df1['Sentence'].apply(get_adr)
    def sep_adr(text):
        adr=[]
        drug=[]
        for i in text:
            
            if i[0]=='ADR':
                adr.append(i[1])
            elif i[0]=='Drug':
                drug.append(i[1])
        adr=",".join(adr)
        drug=",".join(drug)
        
        return (adr,drug)
    (df1['ADR'],df1['DRUG'])=zip(*df1['NER'].apply(sep_adr))
    return df1

def generate_wordcloud(df1,columns):
    df1[columns] = df1[columns].str.lower()
    data = list(df1[columns])
    data = " ".join(data)
    wc=wordcloud.WordCloud(stopwords=STOPWORDS,mode="RGBA",background_color=None,max_words=1000).generate(data)
    return wc.to_image()

@app.route('/upload',methods=['POST','GET'])
def upload():
    if request.method=="POST":
        f=request.files.get("files")
        print(f.filename)
        df = pd.read_csv(f,encoding="ISO-8859-1")
        print(len(df))        
        
        df = get_ner(df)
        adr_c = (df.groupby(['ADR'])['DRUG'].count()).to_dict()
        drug_c = (df.groupby(['DRUG'])['ADR'].count()).to_dict()
        adr_file = generate_wordcloud(df,'ADR')
        img=BytesIO()
        adr_file.save(img,format='PNG')
        adr_img = 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())
        
        drug_file = generate_wordcloud(df,'DRUG')
        img=BytesIO()
        drug_file.save(img,format='PNG')
        drug_img = 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())
        #print(df['ner'])
        df.to_csv("output.csv")
        
    return json.dumps({"message":"Success",'adrs':adr_c,'drugs':drug_c,'adr_wc':adr_img,'drug_wc':drug_img})

@app.route("/download")
def download_output():
    return send_file('output.csv',
                     mimetype='text/csv',
                     attachment_filename='Output-{}.csv'.format(datetime.datetime.now()),
                     as_attachment=True)
if __name__=="__main__":
    app.run(debug=False)