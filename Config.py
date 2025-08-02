import os 

class Config:
   
   @property
   def FUNCTIONS_WORKER_RUNTIME(self):
    return os.environ.get('FUNCTIONS_WORKER_RUNTIME',None)
   
   @property
   def COSMOS_ENDPOINT(self):
    return os.environ.get('COSMOS_ENDPOINT', None)

   @property
   def COSMOS_KEY(self):
    return os.environ.get('COSMOS_KEY', None)

   @property
   def COSMOS_DATABASE_ID(self):
    return os.environ.get('COSMOS_DATABASE_ID', None)

   @property
   def COSMOS_CONTAINER_ID(self):
    return os.environ.get('COSMOS_CONTAINER_ID', None)

   @property
   def AZURE_OPENAI_BASE(self):
    return os.environ.get('AZURE_OPENAI_BASE', None)

   @property
   def AZURE_OPENAI_TYPE(self):
    return os.environ.get('AZURE_OPENAI_TYPE', None)

   @property
   def AZURE_OPENAI_VERSION(self):
    return os.environ.get('AZURE_OPENAI_VERSION', None)

   @property
   def AZURE_OPENAI_KEY(self):
    return os.environ.get('AZURE_OPENAI_KEY', None)

   @property
   def AZURE_OPENAI_MODEL(self):
    return os.environ.get('AZURE_OPENAI_MODEL', None)

   @property
   def COSMOS_EVAL_CONTAINER_ID(self):
      return os.environ.get('COSMOS_EVAL_CONTAINER_ID', None)
   
   @property
   def COSMOS_USER_SESSION_CONTAINER_ID(self):
      return os.environ.get('COSMOS_USER_SESSION_CONTAINER_ID', None)