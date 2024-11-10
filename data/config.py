from environs import Env


env = Env()
env.read_env()

SQL_DATABASE_URL = "sqlite:///./sql_app.db"

BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")
SECRET_KEY = env.str('SECRET_KEY')
WEB_ADMINS = env.list("WEB_ADMINS")
WEB_PASSWORD = env.list("WEB_PASSWORD")
auth_users = dict(map(lambda x: (x[0], x[1]), zip(WEB_ADMINS, WEB_PASSWORD)))
print(auth_users)
CHANNELS = []
with open('group.in', 'r') as file:
    GROUP_ID = file.readline().strip()

api_id = 15414063
api_hash = '24f0849c2f6e13ec792f332e2b771cd0'

regions = {
    1: "Qoraqalpog‘iston Respublikasi",
    2: "Andijon viloyati",
    3: "Buxoro viloyati",
    4: "Jizzax viloyati",
    5: "Qashqadaryo viloyati",
    6: "Navoiy viloyati",
    7: "Namangan viloyati",
    8: "Samarqand viloyati",
    9: "Surxandaryo viloyati",
    10: "Sirdaryo viloyati",
    11: "Toshkent viloyati",
    12: "Farg‘ona viloyati",
    13: "Xorazm viloyati",
    14: "Toshkent shahri"
}
