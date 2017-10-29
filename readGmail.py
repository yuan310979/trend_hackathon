from apiclient import discovery
from apiclient import errors
from httplib2 import Http
from oauth2client import file, client, tools
import base64
from bs4 import BeautifulSoup
import re
import dateutil.parser as parser
from datetime import datetime
import datetime
import json
import requests
import urllib2
from nltk import RegexpTokenizer, word_tokenize
from nltk.corpus import stopwords

SCOPES = 'https://www.googleapis.com/auth/gmail.modify' # we are using modify and not readonly, as we will be marking the messages Read
store = file.Storage('storage.json') 
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))

user_id =  'me'
label_id_one = 'INBOX'
unread_msgs = GMAIL.users().messages().list(userId='me',labelIds=[label_id_one]).execute()

mssg_list = unread_msgs['messages']
print ("Total unread messages in inbox: ", str(len(mssg_list)))
final_list = [ ]

for mssg in mssg_list:
    temp_dict = { }
    m_id = mssg['id'] # get id of individual message
    message = GMAIL.users().messages().get(userId=user_id, id=m_id).execute() # fetch the message using API
    payld = message['payload'] # get payload of the message 
    headr = payld['headers'] # get header of the payload
    for record in headr: # getting the Subject
        if record['name'] == 'Subject':
            msg_subject = record['value']
            temp_dict['Subject'] = msg_subject
        if record['name'] == 'Date':
            msg_date = record['value']
            date_parse = (parser.parse(msg_date))
            m_date = (date_parse.date())
            temp_dict['Date'] = str(m_date)
        if record['name'] == 'From':
            msg_from = record['value']
            temp_dict['Sender'] = msg_from
        if record['name'] == 'Delivered-To':
            msg_to = record['value']
            temp_dict['To'] = msg_to
        else:
            pass
    temp_dict['Snippet'] = message['snippet'] # fetching message snippet
    # Fetching message body
    if 'parts' in payld.keys():
        mssg_parts = payld['parts']
        part_one = mssg_parts
    else:
        part_one = payld
    mssg_body=""
    for r in str(part_one).split("u'body': {u'data':")[1:]:
        part_data = r[3:].split(',')[0][:-1]
        clean_one = part_data.replace("-","+") # decoding from Base64 to UTF-8
        clean_one = clean_one.replace("_","/") # decoding from Base64 to UTF-8
        clean_two = base64.b64decode(bytes(clean_one)) # decoding from Base64 to UTF-8
        mssg_body = mssg_body + clean_two
    """
    try:
        if 'parts' in payld.keys():
            mssg_parts = payld['parts'] # fetching the message parts
            part_one  = mssg_parts[0] # fetching first element of the part
        else:
            part_one = payld
        part_body = part_one['body'] # fetching body of the message
        part_data = part_body['data'] # fetching data from the body
        clean_one = part_data.replace("-","+") # decoding from Base64 to UTF-8
        clean_one = clean_one.replace("_","/") # decoding from Base64 to UTF-8
        clean_two = base64.b64decode(bytes(clean_one)) # decoding from Base64 to UTF-8
    except:
        pass
    """
    if 'In-Reply-To' in temp_dict.keys():
        t= temp_dict['In-Reply-To'][1:-1]
    temp_dict['http_count'] =  mssg_body.count("http://")
    temp_dict['link_count'] =  mssg_body.count("<a href=") + mssg_body.count("<A href=")
    if "<script" in mssg_body:
        temp_dict['has_js'] = 1
    else:
        temp_dict['has_js'] = 0
        
    if 'To' in temp_dict.keys() and temp_dict['To'] == "undisclosed-recipients":
        temp_dict['undisclosed-recipients?'] = 1
    else:
        temp_dict['undisclosed-recipients?'] = 0
        
    
    temp_dict['img_count'] = mssg_body.count("<img src=")
    
    mssg_body = BeautifulSoup(mssg_body, 'html.parser')
    for s in mssg_body(['script', 'style']):
        s.decompose()
    mssg_body = ' '.join(mssg_body.stripped_strings)
    #content['text'] = decode_header(content['text'])[0][0]

    tokenizer = RegexpTokenizer(r'\w+')
    word_tokens = tokenizer.tokenize(mssg_body)
    stop_words = set(stopwords.words('english'))
    
    filtered_sentence = [w for w in word_tokens if not w in stop_words]
    mssg_body = ' '.join(filtered_sentence).encode('utf-8')
    
    temp_dict['Message_body'] = mssg_body
    
    final_list.append(temp_dict)

    json_str = json.dumps(final_list)
    
    # Write json string to local file
    j = json.loads(json_str)
    with open("mail.json", 'wb') as f:
        f.write(json_str)
    
    # Send json to server
    """
    req = urllib2.Request('http://192.168.1.23:123')
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json_str)	
    """
