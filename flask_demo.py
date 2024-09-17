## In the terminal, "export FLASK_APP=flask_demo" (without .py)
## flask run -h 0.0.0.0 -p 8888
import json, operator
import lucene
import re
import os
from datetime import datetime
from org.apache.lucene.store import MMapDirectory, SimpleFSDirectory, NIOFSDirectory
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, IndexOptions, DirectoryReader
from org.apache.lucene.search import IndexSearcher, BoostQuery, Query
from org.apache.lucene.search.similarities import BM25Similarity
from flask import request, Flask, render_template

app = Flask(__name__)      


def loadsFromJson():
    loadFromJson = []
    try:
        with open('./extra.json', 'r') as input:
            loadFromJson = json.load(input)
    except JSONDecodeError:
        print("JSON file is empty.")
    return loadFromJson

def findCommentsAndExternalLinks(submissionId):
    loadFromJson = loadsFromJson()
    for i in loadFromJson:
        if i['id'] == submissionId:
            return [i['comments'], i['titlesForExternalWebpage']]

def create_index(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
    store = SimpleFSDirectory(Paths.get(dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    metaType = FieldType()
    metaType.setStored(True)
    metaType.setTokenized(False)
    
    


    contextType = FieldType()
    contextType.setStored(True)
    contextType.setTokenized(True)
    contextType.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)
    loadFromJson = loadsFromJson()
    for index,post in enumerate(loadFromJson):
        readableTime = convertUnixToTime(post['timeCreated'])

        title = post["title"]
        author = post['author']
        upvotes = post['score']
        postId = post['id']
        body = post['body']
        numOfComments = post['numberOfComments']
        time = post['timeCreated']   
        url = post["url"]
        doc = Document()
        doc.add(Field('url', str(url), metaType))
        doc.add(Field('time', str(readableTime), metaType))
        doc.add(Field('title', str(title), metaType))
        doc.add(Field('position', int(index), metaType))
        doc.add(Field('timeCreated', int(time), metaType))
        doc.add(Field('upvotes', str(upvotes), metaType))
        doc.add(Field('postId', str(postId), metaType))
        doc.add(Field('author', str(author), metaType))
        doc.add(Field('context', str(body), contextType))
        doc.add(Field('numOfComments', str(numOfComments), metaType))
        writer.addDocument(doc)
    writer.close()

def newtopkdocs(listOfDocs):
    print("Scores:")
    for i in listOfDocs:
        print(str(i["score"])+ " " + i["id"])

    print("Old Time:")
    for i in listOfDocs:
        print(str(i['timeCreated'])+ " " + i["id"])
    listOfDocs.sort(key=operator.itemgetter('timeCreated'))
    print("New Time:")
    
    for i in listOfDocs:
        print(str(i['timeCreated'])+ " " + i["id"])
    cnt = 10
    for i in range(1, len(listOfDocs)+1):
        listOfDocs[i-1]["score"] *= (1/cnt)
        cnt -= 1

    listOfDocs.sort(key=operator.itemgetter('score'),reverse = True)
    print("New Scores:")
    for i in listOfDocs:
        print(str(i["score"])+ " " + i["id"])
    


def retrieve(storedir, query):
    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))
    query = re.sub(r'[^a-zA-Z0-9\s]', '', query)
    parser = QueryParser('context', StandardAnalyzer())
    parsed_query = parser.parse(query)
    topDocs = searcher.search(parsed_query, 10).scoreDocs
    topkdocs = []
    loadFromJson = loadsFromJson()

    for hit in topDocs:
        doc = searcher.doc(hit.doc)
        #commentsAndExternalLinks = findCommentsAndExternalLinks(doc.get("postId"))

        

        topkdocs.append({
            "url": doc.get("url"),
            "title": doc.get("title"),
            "id": doc.get("postId"),
           "score": hit.score,
            "upvotes": doc.get("upvotes"),
            "comments": loadFromJson[int(doc.get("position"))]["comments"],
            "externalTitles": loadFromJson[int(doc.get("position"))]["titlesForExternalWebpage"],
            "author": doc.get("author"),
            "context": doc.get("context"),
            "numOfComments": doc.get("numOfComments"),
            "timeCreated": doc.get("timeCreated"),
            "time": doc.get("time")
        })
    #print(topkdocs)
    newtopkdocs(topkdocs)
    return topkdocs

def convertUnixToTime(time):
    dt = datetime.fromtimestamp(time)
    return dt.strftime('%B %d, %Y')
@app.route("/", methods = ['POST', 'GET'])
def home():
    return render_template('input.html')
    

@app.route('/output', methods = ['POST', 'GET'])
def output():
    if request.method == 'GET':
        return f"Nothing"
    if request.method == 'POST':
        form_data = request.form
        query = form_data['query']
        print(f"this is the query: {query}")
        lucene.getVMEnv().attachCurrentThread()
        docs = retrieve('lucene_index/', str(query))
        
        
        return render_template('output.html',lucene_output = docs)
    
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

    
if __name__ == "__main__":
    app.run(debug=True)

create_index('lucene_index/')
#retrieve('lucene_index/', 'web data')


