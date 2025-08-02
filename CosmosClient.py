import azure.cosmos.cosmos_client as cosmos_client
from azure.cosmos.partition_key import PartitionKey
from Config import Config

class CosmosClient:  
    def __init__(self):
        config = Config() 
        self.endpoint = config.COSMOS_ENDPOINT  
        self.key = config.COSMOS_KEY  
        self.database_name = config.COSMOS_DATABASE_ID

        self.client = cosmos_client.CosmosClient(self.endpoint, {'masterKey': self.key})  
        self.database_client = self.client.create_database_if_not_exists(id=self.database_name)  


    @staticmethod
    def get_containerdb_client(self,container_name,partitionKey):       

        try:           
            # Get all containers to check if container exists else create container
            containers = list(self.database_client.query_containers())
            container_names = []
            for container in containers:
                container_names.append(container["id"]) 
            if container_name in container_names:
                container_client = self.database_client.get_container_client(container_name)
            else:               
                partition_key_path = PartitionKey (path = f"/{partitionKey}")            
                container_client = self.database_client.create_container(container_name,partition_key_path) 
            return container_client
        except Exception as e:  
            return None

    @staticmethod
    def create_item(container_client, item):  
    
        # Create the item  
        container_client.upsert_item(body=item) 
        return "successful"
    
    @staticmethod
    def update_item(container_client, item):  
    
        # Create the item  
        container_client.upsert_item(body=item) 
        return "successful"
    
    @staticmethod
    def read_item(container_client, item_id, partition_key):  
        return container_client.read_item(item_id, partition_key=partition_key)
    
    @staticmethod
    def read_items(container_client,query):        
        try:            
            response = container_client.query_items(query=query, enable_cross_partition_query=True)
            items = list(response)
        except Exception as e:
            return None
        return items