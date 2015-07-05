#!/usr/bin/python
#requires pymail, pysftp and sendmail
from __future__ import print_function
import smtplib
from email.mime.text import MIMEText
import glob
import os
import re
import sys
import time
import imp
import pysftp
import logging

reload(sys)
sys.setdefaultencoding('utf8')
path_to_script = os.path.dirname(__file__)
logging.basicConfig(filename=path_to_script + '/last-log.log', level=logging.INFO, format='%(asctime)s %(message)s')

#http://stackoverflow.com/a/924719
def get_variables(filename):
	with open(filename) as f:
	    global conf
	    conf = imp.load_source('data', '', f)

#newfile - file containing new files paths
def send_mail(newfile):
	with open(newfile, 'r') as fp:
		msg = MIMEText("Nalezeny nove soubory: \n" + fp.read())

	msg['Subject'] = "Nalezeny nove soubory"
	msg['From'] = conf.mail_addr_from
	msg['To'] = conf.mail_addr_to
	try:
	   server = smtplib.SMTP(conf.mail_smtp_server)
	   server.login(conf.mail_smtp_user, conf.mail_smtp_pass)
	   server.sendmail(odesilatel, prijemce, msg.as_string())
	   logging.info("Mail byl uspesne odeslan")
	except SMTPException:
	   logging.error("Error: email nemohl byt odeslan")
	server.quit()

#get set containing file1 - file2
def get_file_difference(filename1, filename2):
	with open(filename1, 'r') as file1:
    		with open(filename2, 'r') as file2:
        		return set(file1) - set(file2)

def print_to_file(to_be_printed, fout):
	with open(fout, 'w') as file_out:
		for line in sorted(to_be_printed):
			if not re.match(r'^\s*$', line):
				file_out.write(line)

def walk_and_write(fout, wtcb):
	try:
		with pysftp.Connection(
			host=conf.sftp_host,
			username=conf.sftp_user,
			port=conf.sftp_port,
			private_key=conf.sftp_key_path) as srv:

			# Walk through all paths on server
			srv.walktree(conf.sftp_start_path, fcallback=wtcb.file_cb, dcallback=wtcb.dir_cb, ucallback=wtcb.unk_cb)
			logging.info("Pocet polozek na serveru: " + str(len(wtcb.flist)))
			print(len(wtcb.flist), file=fout)

			# Prints out the directories and files, line by line to file
			for fpath in wtcb.flist:
			    print(fpath.encode('utf-8'), file=fout)
	except pysftp.ConnectionException as e:
		raise e

def main():
	logging.info("Skript spusten")
	get_variables(path_to_script + "/configuration.ini")
	date = time.strftime('%y%m%d%H')
	suffixlist = "_file-list.txt"
	suffixchanges = "_changes.txt"
	filename_list = path_to_script + "/" + date + suffixlist
	filename_changes = path_to_script + "/" + date + suffixchanges
	fout = open(filename_list, 'w')
	files = []
	wtcb = pysftp.WTCallbacks()

	#walktree and write to fout
	try:
		walk_and_write(fout, wtcb)
	except pysftp.ConnectionException as e:
		logging.error("Chyba pripojeni!")
	else:
		for file in glob.glob(path_to_script + "/*" + suffixlist):
			files.append(file)

		if len(files) >= 2:
			files = sorted(files, reverse=True)
			#print to fout changes in last two files
			diff = get_file_difference(files[0], files[1])
			if len(diff) > 1:
				#if any new changes
				logging.info("Nalezeny nove soubory")
				print_to_file(diff, filename_changes)
				send_mail(filename_changes)
	   		else:
	         		logging.info("Nenalezeny zadne nove soubory")
		else:
			logging.info("Nenalezeny predchozi verze stavu.")

main()
