from .message import Message
from .utf import encode as encode_utf7, decode as decode_utf7


class Mailbox():

    def __init__(self, gmail, name=b"INBOX"):
        self.name = name
        self.gmail = gmail
        self.date_format = "%d-%b-%Y"
        self.messages = {}

    @property
    def external_name(self):
        if "external_name" not in vars(self):
            vars(self)["external_name"] = encode_utf7(self.name)
        return vars(self)["external_name"]

    @external_name.setter
    def external_name(self, value):
        if "external_name" in vars(self):
            del vars(self)["external_name"]
        self.name = decode_utf7(value)

    def mail(self, prefetch=False, **kwargs):
        search = [b'ALL']

        kwargs.get(b'read')   and search.append(b'SEEN')
        kwargs.get(b'unread') and search.append(b'UNSEEN')

        kwargs.get(b'starred')   and search.append(b'FLAGGED')
        kwargs.get(b'unstarred') and search.append(b'UNFLAGGED')

        kwargs.get(b'deleted')   and search.append(b'DELETED')
        kwargs.get(b'undeleted') and search.append(b'UNDELETED')

        kwargs.get(b'draft')   and search.append(b'DRAFT')
        kwargs.get(b'undraft') and search.append(b'UNDRAFT')

        kwargs.get(b'before') and search.extend([b'BEFORE', kwargs.get(b'before').strftime(self.date_format)])
        kwargs.get(b'after')  and search.extend([b'SINCE', kwargs.get(b'after').strftime(self.date_format)])
        kwargs.get(b'on')     and search.extend([b'ON', kwargs.get(b'on').strftime(self.date_format)])

        kwargs.get(b'header') and search.extend([b'HEADER', kwargs.get(b'header')[0], kwargs.get(b'header')[1]])

        kwargs.get(b'sender') and search.extend([b'FROM', kwargs.get(b'sender')])
        kwargs.get(b'fr') and search.extend([b'FROM', kwargs.get(b'fr')])
        kwargs.get(b'to') and search.extend([b'TO', kwargs.get(b'to')])
        kwargs.get(b'cc') and search.extend([b'CC', kwargs.get(b'cc')])

        kwargs.get(b'subject') and search.extend([b'SUBJECT', kwargs.get(b'subject')])
        kwargs.get(b'body') and search.extend([b'BODY', kwargs.get(b'body')])

        kwargs.get(b'label') and search.extend([b'X-GM-LABELS', kwargs.get(b'label')])
        kwargs.get(b'attachment') and search.extend([b'HAS', b'attachment'])

        kwargs.get(b'query') and search.extend([kwargs.get(b'query')])

        emails = []
        # print search
        response, data = self.gmail.imap.uid('SEARCH', *search)
        if response == b'OK':
            uids = [_f for _f in data[0].split(' ') if _f] # filter out empty strings

            for uid in uids:
                if not self.messages.get(uid):
                    self.messages[uid] = Message(self, uid)
                emails.append(self.messages[uid])

            if prefetch and emails:
                messages_dict = {}
                for email in emails:
                    messages_dict[email.uid] = email
                self.messages.update(self.gmail.fetch_multiple_messages(messages_dict))

        return emails

    # WORK IN PROGRESS. NOT FOR ACTUAL USE
    def threads(self, prefetch=False, **kwargs):
        emails = []
        response, data = self.gmail.imap.uid('SEARCH', b'ALL')
        if response == 'OK':
            uids = data[0].split(' ')


            for uid in uids:
                if not self.messages.get(uid):
                    self.messages[uid] = Message(self, uid)
                emails.append(self.messages[uid])

            if prefetch:
                fetch_str = ','.join(uids)
                response, results = self.gmail.imap.uid('FETCH', fetch_str, b'(BODY.PEEK[] FLAGS X-GM-THRID X-GM-MSGID X-GM-LABELS)')
                for index in range(len(results) - 1):
                    raw_message = results[index]
                    if re.search(r'UID (\d+)', raw_message[0]):
                        uid = re.search(r'UID (\d+)', raw_message[0]).groups(1)[0]
                        self.messages[uid].parse(raw_message)

        return emails

    def count(self, **kwargs):
        return len(self.mail(**kwargs))

    def cached_messages(self):
        return self.messages
