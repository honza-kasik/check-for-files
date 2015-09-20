#!/usr/bin/env python3
import smtplib
from smtplib import SMTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime
import pysftp
import logging
from tinydb import TinyDB, where
from tinydb.middlewares import SerializationMiddleware
from datetime_serializer import DateTimeSerializer
import configparser


logging.basicConfig(filename='last-log.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def create_db() -> TinyDB:
    """Creates new database with registred datetime serializer"""
    serialization = SerializationMiddleware()
    serialization.register_serializer(DateTimeSerializer(), 'TinyDate')
    db = TinyDB('db.json', storage=serialization)
    return db


# http://stackoverflow.com/a/1432949
def chroot_to_script_location():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)


# http://stackoverflow.com/a/924719
def load_variables(filename):
    global conf
    conf = configparser.ConfigParser()
    conf.read(filename)


def compose_mail(attached_file):
    """Returns composed MimeMultipart"""
    msg = MIMEMultipart()
    text = MIMEText('Nalezeny nove soubory!', 'plain', 'utf8')
    msg.attach(text)

    with open(attached_file, 'r') as f:
        attachment = MIMEText(f.read())
    attachment.add_header('Content-Disposition', 'attachment', filename=attached_file)
    msg.attach(attachment)

    msg['Subject'] = "Nalezeny nove soubory"
    msg['From'] = conf.get('mail', 'from')
    msg['To'] = conf.get('mail', 'to')

    return msg


def send_mail(attachment_file):
    """Sends mail using values specified in conf file"""
    msg = compose_mail(attachment_file)
    server = smtplib.SMTP(conf.get('mail', 'smtp_server'))
    try:
        server.login(conf.get('mail', 'smtp_user'), conf.get('mail', 'smtp_pass'))
        server.sendmail(conf.get('mail', 'from'), conf.get('mail', 'to'), msg.as_string())
        logging.info("Mail was successfully sent!")
    except SMTPException:
        logging.error("Error: mail was not send!")
    finally:
        server.quit()


def get_filepaths_on_server():
    """Return list of files present on server"""
    wtcb = pysftp.WTCallbacks()
    with pysftp.Connection(
            host=conf.get('sftp', 'host'),
            username=conf.get('sftp', 'user'),
            port=int(conf.get('sftp', 'port')),
            private_key=conf.get('sftp', 'key_path')) as server:
        # Walk through all paths on server
        server.walktree(conf.get('sftp', 'start_path'), fcallback=wtcb.file_cb, dcallback=wtcb.dir_cb, ucallback=wtcb.unk_cb)
        logging.info("Count of items on server: " + str(len(wtcb.flist)))

    return wtcb.flist


def walk_and_write_to_db(db: TinyDB):
    """Retrieves paths of all files from server and saves new to database."""
    paths = get_filepaths_on_server()
    for path in paths:
        if not db.contains(where('path') == path):
            db.insert({'path': path, 'datetime': datetime.now()})


def process_new_entries(entries):
    """Processes new entries:
    If there are not any new entries, do nothing, else write them in file and send email
    """
    changes = datetime.strftime('%y%m%d%H') + "_changes.txt"
    if not len(entries) == 0:
        logging.info("Found " + str(len(entries)) + " new files.")
        with open(changes, 'w') as file_out:
            for entry in entries:
                file_out.write(entry['path'])
        send_mail(changes)
    else:
        logging.info("No new files found.")


def main():
    chroot_to_script_location()
    now = datetime.now()
    logging.info("Script started on " + now.strftime('%Y-%m-%dT%H:%M:%S'))
    load_variables("configuration.ini")
    db = create_db()

    try:
        walk_and_write_to_db(db)
    except pysftp.ConnectionException:
        logging.error("Connection error!")
    except IOError:
        logging.error("I/O error during handling with database!")
    else:
        new_entries = db.search(where('datetime' >= now))
        process_new_entries(new_entries)


main()
