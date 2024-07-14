import sys
import os
from app import create_app
from flask.views import View




management = ManagementUtility()
print(management.prog_name)
print(management.argv)
management.executor()