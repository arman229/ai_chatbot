from chainlit.utils import mount_chainlit
from fastapi import FastAPI 
app = FastAPI() 


mount_chainlit(app=app, target="chatbot/my_cl_app.py", path="/") 