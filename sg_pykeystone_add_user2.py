__author__ = 'sebastian'

# Simple script to add users into openstack in a bulk. Users are taken from
# CSV file with following format:
# user_name,user_id,user_email
# Example:
# John Doe,jdoe,jdoe@email.com
#
# CSV file should be in the same directory as executed script
#
# Usage: python sg_pykeystone_add_user.py
#
# Copyright: astianseb
# April, 2014


from keystoneclient.v2_0 import client
from keystoneclient.v2_0 import shell
import csv
import string
import random
import sys
import os
import argparse
import re
from os import path

#USER = os.environ['OS_USERNAME']
#PASS = os.environ['OS_PASSWORD']
#TENANT_NAME = os.environ['OS_TENANT_NAME']
#KEYSTONE_URL = os.environ['OS_AUTH_URL']

# OpenStack params
USER = "admin"
PASS = "205a46188140417b"
TENANT_NAME = "admin"
KEYSTONE_URL = "http://173.36.55.54:35357/v2.0/"

BULK_TENANT = 'openstack'
BULK_TENANT_DESC = 'Tenant created by script'

def is_username_valid(username):
    regex = re.compile(r"^\w+@gmail.com$")
    if regex.match(username):
        return True
    return False

def password_generator():
    password = []
    for i in range(10):
        password.append(random.choice(string.hexdigits))
    return "".join(password)

def send_email(user_name, user_id, password, email):
    import smtplib

    gmail_user = GMAIL_USER
    gmail_pwd = GMAIL_PASSWORD
    USER = user_name
    USER_ID = user_id
    PASS = password
    FROM = GMAIL_USER
    TO = [email] #must be a list
    SUBJECT = "New OS account created"
    TEXT = """Hello %s!
    \nWe have created new account.
    \nYour login details are:\nu:%s\np:%s
    \nPlease log in and check whether it works properly.\nMessage sent by script""" % (USER, USER_ID, PASS)

    # Prepare actual message
    message = "From: %s\nTo: %s\nSubject: %s\n%s" % (FROM, ", ".join(TO), SUBJECT, TEXT)
    print message
    try:
        #server = smtplib.SMTP(SERVER)
        server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        #server.quit()
        server.close()
        print 'successfully sent the mail to %s' % USER
    except:
        print "failed to send mail"




class SGkeystone:

    def __init__(self, kc):
        self.keystone = kc

    def get_tenant_users(self, tenant_id):
        return self.keystone.tenants.list_users(tenant_id)

    def get_tenant(self, tenant_id):
        return self.keystone.get(tenant_id)

    def get_tenant_list(self):
       return self.keystone.tenants.list()

    def _get_tenant_name(self, tenant_id):
        for i in self.get_tenant_list():
            if i.id == tenant_id:
                return i.name

    def _get_tenant_id(self, tenant_name):
        for i in self.get_tenant_list():
            if i.name == tenant_name:
                return i.id

    def is_tenant_configured(self, tenant_name):
        for i in self.keystone.tenants.list():
            if i.name == tenant_name:
                return True
        else:
            return False

    def is_user_configured(self, tenant_name, user_name):
        tenant_id = self._get_tenant_id(tenant_name)
        for i in self.keystone.tenants.list_users(tenant_id):
            if i.name == user_name:
                return True
        else:
            return False

#
#
#
class Namespace:
    ''' Fake class needed to create a namespace for shell library. In normal
      keystoneclient use - number of parameters are passed in command line. Keystoneclient
      is leveraging argparse - and argparse is using namespace as a data structure. In here
      we're using only part of parameters. The others are:
      self.debug = False
      self.force_new_token = False
      self.func = <function do_user_list at 0x2909b18>
      self.help = False
      self.insecure = False
      self.os_cacert = None
      self.os_cache = False
      self.os_cert = ''
      self.os_endpoint = ''
      self.os_identity_api_version = ''
      self.os_key = ''
      self.os_region_name = ''
      self.os_tenant_id = ''
      self.os_token = ''
      self.os_username = 'admin'
      self.stale_duration = 30
      self.tenant_id = None
      self.timeout = 600
    '''

    def __init__(self, user=None, tenant=None):
        self.tenant = tenant
        self.os_auth_url = KEYSTONE_URL
        self.os_password = PASS
        self.os_tenant_name = TENANT_NAME
        self.os_username = USER
        self.user = user


#
# Command line parser
#

parser = argparse.ArgumentParser(description='Script adding users to openstack in a bulk from CSV file')
parser.add_argument('username', help='Gmail username eq. johndoe@gmail.com')
parser.add_argument('password', help='Gmail password')
parser.add_argument('file', help='CSV file')
cmdl_args = parser.parse_args()
if not is_username_valid(cmdl_args.username):
    print "BAD email!"
    sys.exit(0)

if not path.isfile(cmdl_args.file):
    print "CSV file does not exist!"
    sys.exit(0)

GMAIL_USER = cmdl_args.username
GMAIL_PASSWORD = cmdl_args.password
CSVFILE = cmdl_args.file

args = Namespace()

try:
    with open(CSVFILE) as csvfile:
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=',')
        except csv.Error:
            print "Error reading CSV or wrong CSV format"
            sys.exit(0)
except IOError:
    print "Wrong CSV file or file does not exist!"
    sys.exit(0)


kc = client.Client(username=USER,
                             password=PASS,
                             tenant_name=TENANT_NAME,
                             auth_url=KEYSTONE_URL)


obj = SGkeystone(kc)

if not obj.is_tenant_configured(BULK_TENANT):
    obj.keystone.tenants.create(tenant_name=BULK_TENANT,
                        description=BULK_TENANT_DESC, enabled=True)
    print "Tenant %s created" % BULK_TENANT
    shell.do_tenant_get(kc, Namespace(tenant=BULK_TENANT))
else:
    print 'Tenant %s already exist!' % BULK_TENANT
    shell.do_tenant_get(kc, Namespace(tenant=BULK_TENANT))


with open(CSVFILE) as csvfile:
    users_reader = csv.reader(csvfile)
    users_list = {}
    for i in users_reader:
        user_name = i[0]
        user_id = i[1]
        user_email = i[2]


        user_pass = password_generator()

        if not obj.is_user_configured(BULK_TENANT, user_id):
            obj.keystone.users.create(name=user_id,
                                      password=user_pass,
                                      email=user_email,
                                      tenant_id=obj._get_tenant_id(BULK_TENANT))
            print "User %s created. u:%s p:%s" % (user_id, user_id, user_pass)
            shell.do_user_get(kc,Namespace(user=user_id))
            send_email(user_name, user_id, user_pass, user_email)
        else:
            print "User %s already exist!" % user_id
            shell.do_user_get(kc,Namespace(user=user_id))

    print "List of users available under tenant: %s" %BULK_TENANT
    shell.do_user_list(kc,Namespace(tenant=BULK_TENANT))
