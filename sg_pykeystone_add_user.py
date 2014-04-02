__author__ = 'sebastian'

from keystoneclient.v2_0 import client
import csv
import string
import random
import sys
import os

USER = os.environ['OS_USERNAME']
PASS = os.environ['OS_PASSWORD']
TENANT_NAME = os.environ['OS_TENANT_NAME']
KEYSTONE_URL = os.environ['OS_AUTH_URL']

#USER = "admin"
#PASS = "0641540afdcb4e91"
#TENANT_NAME = "admin"
#KEYSTONE_URL = "http://172.29.68.13:35357/v2.0/"
CSVFILE = "user_names_emails.csv"

BULK_TENANT = 'openstack'
BULK_TENANT_DESC = 'Tenant created by script'

def password_generator():
    password = []
    for i in range(10):
        password.append(random.choice(string.hexdigits))
    return "".join(password)



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
else:
    print 'Tenant %s already exist!' % BULK_TENANT


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
        else:
            print "User %s already exist!" % user_id
