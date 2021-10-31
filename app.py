from os import name
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
from block import Block
import datetime
import random
import requests
import xml.etree.ElementTree as ET
import json
import base64
from PIL import Image
import xml.dom.minidom
import mysql.connector as connector
from dns.resolver import query
import os
import xml.etree.ElementTree as ET #importing xml.etree.ElementTree module which implements a simple and efficient API for parsing

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

socketio = SocketIO(app, manage_session=False)

@app.route('/', methods=['GET', 'POST'])
def login():
    api_url = "https://stage1.uidai.gov.in/unifiedAppAuthService/api/v2/get/captcha"
    todo = { "langCode": "en", "captchaLength": "3", "captchaType": "2" }
    headers =  {"Content-Type":"application/json"}
    response = requests.post(api_url, data=json.dumps(todo), headers=headers)
    p=response.json()
    
    '''json_object = json.dumps(p, indent=4)

    # Writing to sample.json
    with open("sample.json", "w") as outfile:
        outfile.write(json_object)'''
        
    data = p
    # Iterating through the json
    # list
    k=data['captchaBase64String']
    # print(k)
    imgdata = base64.b64decode(k)
    filename = 'some_image.jpg' # I assume you have a way of picking unique filenames
    with open(filename, 'wb') as f:
        f.write(imgdata)
    im = Image.open(r"some_image.jpg")
    im.save(r'static/recaptcha.jpg')
    id=data['captchaTxnId']
    print(id)
    session['my_var'] = id
    return render_template('login.html')

@app.route('/otp', methods=['GET', 'POST'])
def otp():
    id = session.get('my_var', None)
    # print(str(id))
    captcha=request.form['recaptcha']
    aadharnum=request.form['number']
    session['my'] = aadharnum
    # otp generation
    url = "https://stage1.uidai.gov.in/unifiedAppAuthService/api/v2/generate/aadhaar/otp"
    payload = json.dumps({
    "uidNumber": aadharnum, # 999986895578
    "captchaTxnId": id,
    "captchaValue": captcha,
    "transactionId": "MYAADHAAR:b8b5b7df-d224-4956-8eb3-6a4fb8f0c236"
    })
    headers = {'x-request-id': 'b8b5b7df-d224-4956-8eb3-6a4fb8f0c236','appid': 'MYAADHAAR','Accept-Language': 'en',
    'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    q=response.json()
    c=q['txnId']
    session['var']=c
    print(captcha)
    print(id)
    print(aadharnum)
    return render_template('otp.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    random_string = ''
    for _ in range(6):
        # Considering only upper and lowercase letters
        random_integer = random.randint(97, 97 + 26 - 1)
        flip_bit = random.randint(0, 1)
        # Convert to lowercase if the flip bit is on
        random_integer = random_integer - 32 if flip_bit == 1 else random_integer
        # Keep appending random characters using chr(x)
        random_string += (chr(random_integer))
    # print(random_string)
    
    #EKYC generation
    # c=q['txnId']
    c=session.get('var', None)
    aadharnum=session.get('my', None)
    url = "https://stage1.uidai.gov.in/eAadhaarService/api/downloadOfflineEkyc"
    inp=request.form['otp']
    payload = json.dumps({
    "txnNumber": c,
    "otp": inp,
    "shareCode": "4567",
    "uid": aadharnum
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    output=response.json()
    json_object = json.dumps(output, indent=4)

    # Writing to sample.json
    with open("sample2.json", "w") as outfile:
        outfile.write(json_object)

    # CONVERTING JOSN INTO XML FILE
    f = open('sample2.json',"r")
    data = json.load(f)
    b64 =data['eKycXML']
    file = data['fileName']
    x = file.split(".")
    z = x[0]
    encoded = b64
    decoded = base64.b64decode(encoded)
    filename = 'ekycaadhar.zip'
    with open(filename, 'wb') as f:
        f.write(decoded)

    #Extracting the files
    payload = json.dumps({
    "txnNumber": "888",
    "otp": "000",
    "shareCode": "4567",
    "uid": aadharnum
    })
    payload=json.loads(payload)

    n=payload["shareCode"]
    
    pswd=n
    pswd=pswd.encode()
    from zipfile import ZipFile
    file_name = "ekycaadhar.zip"
    with ZipFile(file_name, 'r') as zip:
        zip.printdir()
        print('Extracting all the files now...')
        zip.extractall(None,None,pswd)
        print('Done!')
    if os.path.exists('tenant.xml'):
        os.rename(f"{z}.xml",'landlord.xml')
    else:
        os.rename(f"{z}.xml",'tenant.xml')
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if(request.method=='POST'):
        username = request.form['username']
        room = request.form['room']
        #Store the data in session
        session['username'] = username
        session['room'] = room
        return render_template('chat.html', session = session)
    else:
        if(session.get('username') is not None):
            return render_template('chat.html', session = session)
        else:
            return redirect(url_for('index'))
        
@app.route('/claim', methods=['GET', 'POST'])
def claim():
    username=session.get('username', None)
    return render_template('claim.html', username = username)

@app.route('/claimed', methods=['GET', 'POST'])
def claimed():
    tree = ET.parse('tenant.xml')
    root=tree.getroot()
    listold={}
    for index in root.findall("./UidData/Poa"):
        listold=(index.attrib)
    key_list=list(listold.keys())
    val_list=list(listold.values())
    wanted=["house","street","vtc","dist","state","pc"]
    n=""
    for i in range(6):
        k=wanted[i]
        for j in range(12):
            h=key_list[j]
            if(k==h):
                n+=val_list[j]+" "
    print(n)    
    return render_template('claimed.html', address=n)

@app.route('/requestInbox', methods=['GET', 'POST'])
def requestInbox():
    return render_template('requestInbox.html')

@app.route('/landlordIndex', methods=['GET', 'POST'])
def landlordIndex():
    return render_template('landlordIndex.html')

@app.route('/claimInbox', methods=['GET', 'POST'])
def claimInbox():
    return render_template('claimInbox.html')

@app.route('/landlordapproval', methods=['GET', 'POST'])
def landlordapproval():
    return render_template('landlordapproval.html')

@app.route('/userIndex', methods=['GET', 'POST'])
def userIndex():
    return render_template('userIndex.html')

@app.route('/updated', methods=['GET', 'POST'])
def updated():
    tree = ET.parse('tenant.xml')
    root=tree.getroot()
    list={}
    for index in root.findall("./UidData/Poa"):
        list=(index.attrib)
    house = request.form['house']
    print(house)
    list['house'] = house
    tree.write("tenant.xml")
    doc=xml.dom.minidom.parse("tenant.xml")
    #print (doc.nodeName)
    m=""
    expertise=doc.getElementsByTagName("Poa")[0]
    m = expertise.getAttribute("house")+", "+expertise.getAttribute("street")+", "+expertise.getAttribute("landmark")+", "+expertise.getAttribute("vtc")+", "+expertise.getAttribute("po")+", "+expertise.getAttribute("subdist")+", "+expertise.getAttribute("dist")+", "+expertise.getAttribute("state")+", "+expertise.getAttribute("country")+", "+expertise.getAttribute("pc")+"."
    print(m)
    return render_template('updated.html', address=m)

@app.route('/approved', methods=['GET', 'POST'])
def approved():
    #uploading landlord's and tentant's xml files in landlord and tenant variable respectively
    landlord= ET.parse("landlord.xml")
    tenant=ET.parse("tenant.xml")
    #storing their root element in landlord_root and tenant_root respectively 
    landlord_root = landlord.getroot()
    tenant_root = tenant.getroot()

    #displaying the attributes of Poa element node for landlord xml file
    for index in landlord_root.findall("./UidData/Poa"):
        print(index.attrib)
    #displaying the attributes of Poa element node for tenant xml file
    for index in tenant_root.findall("./UidData/Poa"):
        print(index.attrib)

    #creating an empty list
    list_one={}
    #since attribute careof should not be changed storing the attribute in the created list
    for index in tenant_root.findall("./UidData/Poa"):
        list_one=index.attrib
    #now the careof attribute's value is stored in a variable value_of_careof 
    value_of_careof=list(list_one.values())[0]

    #creating a new list named list_two
    list_two={}
    #stroting all the attributes of the landlord's Poa in the created list_two
    for index in landlord_root.findall("./UidData/Poa"):
        list_two=index.attrib
        print(list_two)
    #swapping the attributes of Poa of landlord to the tenant 
    for index in tenant_root.findall("./UidData/Poa"): 
        index.attrib=list_two;
    #now changing the value of careof in the tenant file with the value_of_careof 
    for i,j in list_two.items():
        if i == "careof":
            list_two[i] = value_of_careof
    #displaying the tenant attributes of Poa
    for index in tenant_root.findall("./UidData/Poa"): 
        index.attrib=list_two;

    #new changes made are updated as a new xml file 
    tenant.write("tenant.xml")
    tenant= ET.parse("tenant.xml")
    return render_template('approved.html')

@app.route('/viewStatus', methods=['GET', 'POST'])
def viewStatus():
    tree = ET.parse('tenant.xml')
    root=tree.getroot()
    listold={}
    for index in root.findall("./UidData/Poa"):
        listold=(index.attrib)
    key_list=list(listold.keys())
    val_list=list(listold.values())
    wanted=["house","street","vtc","dist","state","pc"]
    n=""
    for i in range(6):
        k=wanted[i]
        for j in range(12):
            h=key_list[j]
            if(k==h):
                n+=val_list[j]+","+" "
    print(n)
    return render_template('viewStatus.html', address = n)

@app.route('/editaddress', methods=['GET', 'POST'])
def editAddress():
    tree = ET.parse('tenant.xml')
    root=tree.getroot()
    list={}
    for index in root.findall("./UidData/Poa"):
        list=(index.attrib)
    house = list['house']
    street = list['street']
    vtc = list['vtc']
    landmark = list['landmark']
    po = list['po']
    subdist = list['subdist']
    dist = list['dist']
    pc = list['pc']
    state = list['state']
    country =list['country']
    return render_template('editaddress.html', house=house, street=street, vtc=vtc, landmark=landmark, po=po, subdist=subdist, dist=dist, pc=pc, state=state, country=country)

@socketio.on('join', namespace='/chat')
def join(message):
    room = session.get('room')
    join_room(room)
    emit('status', {'msg':  session.get('username') + ' has entered the room.'}, room=room)

@socketio.on('text', namespace='/chat')
def text(message):
    block_chain = [Block.create_genesis_block()]
    room = session.get('room')
    hashed = block_chain[-1].hash
    
    # Appends To The DB
    con = connector.connect(host='localhost',
                user='root',
            password='jesus10*',
            database='aadhaar')
    query = 'create table if not exists chat(hash varchar(400) primary key)'
    cur = con.cursor()
    cur.execute(query)
    print("Created")
    query = 'insert into chat values("'+hashed+'")'
    print(query)
    cur = con.cursor()
    cur.execute(query)
    cur.close()
    con.commit()
    print("Message Hash Saved To The Chat DB")
    
    emit('message', {'msg': session.get('username') + ' : ' + message['msg'] + " \nHash: %s" % hashed}, room=room)
    
@socketio.on('left', namespace='/chat')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)

if __name__ == '__main__':
    socketio.run(app)