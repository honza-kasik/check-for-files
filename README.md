# check-for-files
Simple python script to retrieve filepaths from sftp server and send alert email with new filepaths.

##Requirements

* **Python 3**
* Packages:
  * `email` - email composing
  * `smtplib` - sending email
  * `pysftp` - sftp related operations
  * `tinydb` - filepaths storage and handling
