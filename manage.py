import sys
import os
from django.core.management import ManagementUtility

from app import create_app


app = create_app()


def main():
    app.run(debug=True)
    
        
if __name__=="__main__":
    main()