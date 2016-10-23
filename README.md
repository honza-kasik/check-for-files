# check-for-files
Simple python script to retrieve filepaths from SFTP server and send alert email with new filepaths. After each start of script it walks the filetree, compares it to already saved items and sends an email notification to configured email address if there are any new files. TinyDB is used to store changes locally.

This script is probalby only useful to you, when you have no other access to server than SFTP, as in my case. 

## Configuration

First of all you have to replace example configuration in `configuration.ini` by your setting.

```
[mail]
from: user@foo.qiz        //From which address will be emails sent
to: target@bar.qux        //To which address will be email sent
smtp_server: smtp.foo.qiz //smtp server for sending emails
smtp_user: user@foo.qiz   //Your user name for smtp server
smtp_pass: password       //Your password for smtp server
[sftp]
host: host.company.com    //SFTP server which will be checked for new files
user: user                //User at SFTP server
port: 22                  //Port of SFTP server
key_path: /home/user/.ssh/id_dsa //Path to private ssh key for authentication
start_path: /             //Path on which the script starts recursive searching
```

## How to run

`./check-for-files.py`

### Requirements

* **Python 3**
* Packages:
  * `email` - email composing
  * `smtplib` - sending email
  * `pysftp` - sftp related operations
  * `tinydb` - filepaths storage and handling
