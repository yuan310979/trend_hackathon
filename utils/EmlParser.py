import os, glob, re, csv, codecs
from email import message_from_file
from email.header import decode_header
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from bs4 import BeautifulSoup

# Path to directory where attachments will be stored:
path = './10'

# To have attachments extracted into memory, change behaviour of 2 following functions:
def file_exists(f):
    return os.path.exists(os.path.join(path, f))

def save_file(fn, cont):
    file = open(os.path.join(path, fn), 'wb')
    file.write(cont)
    file.close()

def construct_name(id, fn):
    id = id.split('.')
    id = id[0] + id[1]
    return id + '.' + fn

def disqo(s):
    s = s.strip()
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s

def disgra(s):
    s = s.strip()
    if s.startswith('<') and s.endswith('>'):
        return s[1:-1]
    return s

def pullout(m, key):
    Html = ''
    Text = ''
    Files = {}
    if not m.is_multipart():
        if m.get_filename():
            fn = m.get_filename()
            cfn = construct_name(key, fn)
            Files[fn] = (cfn, None)
            if file_exists(cfn):
                return Text, Html, Files
            save_file(cfn, m.get_payload(decode=True))
            return Text, Html, Files

        cp = m.get_content_type()
        if cp == 'text/plain':
            Text += m.get_payload(decode=True)
        elif cp == 'text/html':
            Html += m.get_payload(decode=True)
        else:
            cp = m.get('content-type')
            try:
                id = disgra(m.get('content-id'))
            except:
                id = None
            # Find file name:
            o = cp.find('name=')
            if o == -1:
                return Text, Html, Files
            ox = cp.find(';', o)
            if ox == -1:
                ox = None
            o += 5
            fn = cp[o:ox]
            fn = disqo(fn)
            cfn = construct_name(key, fn)
            Files[fn] = (cfn, id)
            if file_exists(cfn):
                return Text, Html, Files
            save_file(cfn, m.get_payload(decode=True))
        return Text, Html, Files

    y = 0
    while 1:
        # If we cannot get the payload, it means we hit the end:
        try:
            pl = m.get_payload(y)
        except:
            break
        t, h, f = pullout(pl, key)
        Text += t
        Html += h
        Files.update(f)
        y += 1
    return Text, Html, Files

def extract(msgfile, key):
    m = message_from_file(msgfile)
    From, To, Subject, Spam, Sender, Reply = caption(m)
    Text, Html, Files = pullout(m, key)
    Text = Text.strip()
    Html = Html.strip()
    msg = {
        'subject': Subject,
        'from': From,
        'to': To,
        'sender': Sender,
        'text': Text,
        'html': Html,
        'spam': Spam,
        'reply': Reply
    }
    if Files:
        msg['files'] = Files
    return msg

def caption(origin):
    From = ''
    if origin.has_key('from'):
        From = origin['from'].strip()
    To = ''
    if origin.has_key('to'):
        To = origin['to'].strip()
    Subject = ''
    if origin.has_key('subject'):
        Subject = origin['subject'].strip()
    Spam = ''
    if origin.has_key('X-Spam-ISSPAM-FLAG'):
        Spam = origin['X-Spam-ISSPAM-FLAG'].strip()
    Sender = ''
    if origin.has_key('sender'):
        Sender = origin['sender'].strip()
    Reply = ''
    if origin.has_key('Reply-to: '):
        Reply = origin['Reply-to: '].strip()
    return From, To, Subject, Spam, Sender, Reply

def find_urls(text):
    url_reg = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_reg, text)
    return urls

def parse_eml(content):
    hidden_urls = find_urls(content['text'] + ' ' + content['html'])

    count_https = 0
    for url in hidden_urls:
        if url in content['text']:
            content['text'] = content['text'].replace(url, '')
        elif url in content['html']:
            content['html'] = content['html'].replace(url, '')

        if 'https' in url:
            count_https += 1

    content['num_of_link'] = len(hidden_urls)
    content['num_of_url_is_http'] = len(hidden_urls) - count_https

    if '<script' in content['html'] or '<script' in content['text']:
        content['has_JS'] = 1
    else:
        content['has_JS'] = 0

    if '<img src' in content['html'] or '<img src' in content['text']:
        content['has_url_based_image_source'] = 1
    else:
        content['has_url_based_image_source'] = 0

    content['text'] = content['text'] + ' ' + content['html']
    if content['text']:
        content['text'] = BeautifulSoup(content['text'], 'html.parser')
        for s in content['text'](['script', 'style']):
            s.decompose()
        content['text'] = ' '.join(content['text'].stripped_strings)
        #content['text'] = decode_header(content['text'])[0][0]

        tokenizer = RegexpTokenizer(r'\w+')
        word_tokens = tokenizer.tokenize(content['text'])
        stop_words = set(stopwords.words('english'))

        filtered_sentence = [w for w in word_tokens if not w in stop_words]

        if 'base64' in filtered_sentence:
            filtered_sentence = filtered_sentence[12:]
            filtered_sentence = [f for f in filtered_sentence if len(f) < 20]
        content['text'] = ' '.join(filtered_sentence).encode('utf-8')

    if content['subject']:
        content['subject'] = decode_header(content['subject'])[0][0]
        tokenizer = RegexpTokenizer(r'\w+')
        word_tokens = tokenizer.tokenize(content['subject'])
        stop_words = set(stopwords.words('english'))

        filtered_sentence = [w for w in word_tokens if not w in stop_words]

        content['subject'] = ' '.join(filtered_sentence)

    if (content['sender'] not in content['from']) and (content['from'] not in content['sender']):
        content['inconsistency'] = 1
    else:
        content['inconsistency'] = 0

    if content['reply'] != content['from']:
        content['has_reply_to_others'] = 1
    else:
        content['has_reply_to_others'] = 0

    if content['to'] == 'undisclosed-recipients':
        content['to_undisclosed-recipients'] = 1
    else:
        content['to_undisclosed-recipients'] = 0

    '''
    if content['spam'] == 'Yes':
        content['spam'] = 1
    else:
        content['spam'] = 0
    '''
    content['spam'] = 1

    content.pop('from', None)
    content.pop('to', None)
    content.pop('sender', None)
    content.pop('html', None)
    content.pop('reply', None)

    return content

def iter_files(path):
    parse_result = []

    eml_files = glob.glob(path)
    for eml in eml_files:
        try:
            #print(eml)
            file = codecs.open(eml, 'rb', encoding='utf-8', errors='ignore')
            content = extract(file, file.name)
            #print(content)
            content = parse_eml(content)
            parse_result.append(content)
            file.close()
        except:
            pass

    return parse_result

def main():
    output = iter_files(path + '/*')
    # output = iter_files(path + '/Sample_000001_00000001.eml')

    output_csv = output
    #print(output_csv)
    keys = output_csv[0].keys()
    with open('eml_parse_spam.csv', 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(output_csv)

if __name__ == "__main__":
    main()
