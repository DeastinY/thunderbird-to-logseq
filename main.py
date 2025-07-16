import mailbox
import email
import os
import re
from email.utils import parsedate_to_datetime

def clean_filename(s):
    return re.sub(r'[^\w\-_. ]', '_', s)

def email_to_markdown(msg):
    subject = msg.get('subject', 'No Subject')
    sender = msg.get('from', 'Unknown Sender')
    # Format sender as [[Name]] (email)
    sender_name, sender_email = email.utils.parseaddr(sender)
    if sender_name and sender_email:
        # Swap "Last, First" to "First Last" if comma is present
        if ',' in sender_name:
            last, first = [part.strip() for part in sender_name.split(',', 1)]
            formatted_name = f"{first} {last}"
        else:
            formatted_name = sender_name
        sender = f"[[{formatted_name}]] ({sender_email})"
    elif sender_email:
        sender = f"({sender_email})"
    else:
        sender = "Unknown Sender"
    date_raw = msg.get('date', 'Unknown Date')

    try:
        date_obj = parsedate_to_datetime(date_raw)
        date = f"[[{date_obj.strftime('%Y-%m-%d')}]]"
    except Exception:
        date = '[[Unknown Date]]'

    to = msg.get('to', 'Unknown Recipient')

    # Get plain text part of the email
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'), errors='replace')
                break
    else:
        body = msg.get_payload(decode=True).decode(msg.get_content_charset('utf-8'), errors='replace')

    markdown = f"""[[Mail]] # {subject}

**From:** {sender}  
**To:** {to}  
**Date:** {date}  

---

{body}
"""
    return markdown

def convert_mbox_to_markdown(mbox_file, output_dir='emails_markdown'):
    os.makedirs(output_dir, exist_ok=True)
    mbox = mailbox.mbox(mbox_file)
    
    cache_file = os.path.join(output_dir, '.exported_emails_cache')
    exported_ids = set()
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as cf:
            exported_ids = set(line.strip() for line in cf if line.strip())

    new_exported_ids = set()

    for i, msg in enumerate(mbox):
        msg_id = msg.get('message-id')
        if not msg_id:
            # Fallback: use subject + date as a weak identifier
            msg_id = f"{msg.get('subject', '')}_{msg.get('date', '')}"
        msg_id = msg_id.strip()
        if msg_id in exported_ids:
            continue
        md_content = email_to_markdown(msg)
        subject = msg.get('subject', f'email_{i}')
        filename = clean_filename(subject)[:50] + '.md'
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"Saved: {filepath}")
        new_exported_ids.add(msg_id)

    if new_exported_ids:
        with open(cache_file, 'a', encoding='utf-8') as cf:
            for msg_id in new_exported_ids:
                cf.write(msg_id + '\n')

if __name__ == "__main__":
    output_dir = "/home/USERNAME/logseq/emails/"

    for mbox_file in [
        "~/.thunderbird/PROFILEID.default/ImapMail/MYMAILACCOUNT/INBOX",
        "~/.thunderbird/PROFILEID.default/ImapMail/MYMAILACCOUNT/important"
    ]:
        print(f"Processing: {mbox_file}")
        convert_mbox_to_markdown(mbox_file, output_dir)

