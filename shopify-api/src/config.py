import os
basedir = os.path.abspath(os.path.dirname(__file__))

APP_SECRET_KEY='DSIA$319'

SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'app.db')

SHOPIFY_API_KEY = "62db2d22aedb3c9774995cc9ec40a068"
SHOPIFY_SECRET = "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"

APP_NAME = "video-lessons-plugin"
DOMAIN='insta-tag-checker.xyz'
SERVER_HOSTNAME = F"{DOMAIN}/api"
SERVER_BASE_URL = f"https://{SERVER_HOSTNAME}"
SERVER_DOMAIN=f'https://{DOMAIN}'
INSTALL_REDIRECT_URL = f"{SERVER_BASE_URL}/app_installed"

WEBHOOK_APP_UNINSTALL_URL = f"https://{SERVER_HOSTNAME}/app_uninstalled/"
WEBHOOK_ORDER_CREATED_URL=f"https://{SERVER_HOSTNAME}/order_paid/"
WEBHOOK_PRODUCT_ADDED_URL=f"https://{SERVER_HOSTNAME}/product_added/"

TWILIO_ACCOUNT_SID='AC115b9f3459e887c89d83303a6431b6a4'
TWILIO_API_KEY_SID='SK706de4a3e10adddfcfe50cbd1df9fc47'
TWILIO_API_KEY_SECRET='vX1beQOtHd6QcwF023nJ8daHmNmyubeb'

DEFAULT_EMAIL_TEMPLATE='Thank you for your purchase! /// Thank you for your purchase! Please visit <<LINK>>. Date: <<DATE>>. Pass: <<PASSWORD>>. /// <body></body>'
EMAIL_USERNAME='buku.test.acc@gmail.com'
EMAIL_PASS='splash99'