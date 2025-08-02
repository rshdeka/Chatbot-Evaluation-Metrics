import logging
import json
from Config import Config
from CosmosClient import CosmosClient
import azure.functions as func
from qna_scores import fetch_conversation, calculate_qna_scores


qna_processing_blueprint=func.Blueprint()


def process_qna_evaluation(conversation_id, query_id, response_id, context_id):
    config = Config()  
    cosmos_client = CosmosClient()  
    cosmos_conversation_evaluation_client = cosmos_client.get_containerdb_client(cosmos_client, config.COSMOS_EVAL_CONTAINER_ID,"id")

    # Fetch the specific conversation
    cosmos_conversation_client = cosmos_client.get_containerdb_client(cosmos_client, config.COSMOS_CONTAINER_ID, "userId")  
    conversation = fetch_conversation(cosmos_client, cosmos_conversation_client, conversation_id)  
    if not conversation:  
        logging.info("Conversation not found.")  
        return {"error": f"Provided Conversation ID not found."}
    
    # Check if context ID is provided  
    if context_id:  
        # Check if query, response, and context message exist in the conversation  
        if not any(msg["messageId"] == query_id for msg in conversation["messages"]) or not any(msg["messageId"] == response_id for msg in conversation["messages"]):  
            logging.info("Query or Response message not found in the conversation.")  
            return {"error": f"Provided Query or Response message doesn't exist within this Conversation."}
        if not any(msg["messageId"] == context_id for msg in conversation["messages"]):  
            logging.info("Context message not found in the conversation.")  
            return {"error": f"Provided Context ID doesn't exist within this Conversation."} 
    else:  
        # Check if query and response message exist in the conversation  
        if not any(msg["messageId"] == query_id for msg in conversation["messages"]) or not any(msg["messageId"] == response_id for msg in conversation["messages"]):  
            logging.info("Query or Response message not found in the conversation.")  
            return {"error": f"Provided Query or Response message doesn't exist within this Conversation."} 

    # Call the calculate_qna_scores function to get the scores  
    evaluated_message = calculate_qna_scores(conversation_id, query_id, response_id, context_id)

    # Filter out null scores  
    evaluated_message["scores"] = {k: v for k, v in evaluated_message["scores"].items() if v is not None} 
    
    # Fetch existing conversation if it exists  
    existing_conversation = fetch_conversation(cosmos_client, cosmos_conversation_evaluation_client, conversation_id)  

    if existing_conversation:
        logging.info(f"Conversation ID {conversation_id} found.")
        logging.info("Checking for duplicate evaluations.")  

        # Check if this particular evaluation already exists  
        if any(  
            em["query_id"] == evaluated_message["query_id"] and  
            em["response_id"] == evaluated_message["response_id"] and  
            em["context_id"] == evaluated_message["context_id"]  
            for em in existing_conversation["evaluated_message"]  
        ):  
            logging.info("Duplicate evaluation found. Skipping append.") 
            return {"message": "Duplicate evaluation found. Skipping append."}  
        else:  
            logging.info("No duplicate found. Appending evaluation.")  
            
            # If this particular message evaluation doesn't exist within that conversation, append it
            existing_conversation["evaluated_message"].append(evaluated_message)  
            cosmos_client.update_item(cosmos_conversation_evaluation_client, existing_conversation)  
        
        # If conversation ID already exists, append the message evaluation scores within that same item
        cosmos_client.update_item(cosmos_conversation_evaluation_client, existing_conversation)  
    else:  
        logging.info(f"Conversation ID {conversation_id} not found. Creating new conversation entry.")

        # Fetch additional details from the original conversation
        cosmos_conversation_client = cosmos_client.get_containerdb_client(cosmos_client, config.COSMOS_CONTAINER_ID, "userId")  
        original_conversation = fetch_conversation(cosmos_client, cosmos_conversation_client, conversation_id)  
            
        if not original_conversation: 
            return {"error": "Provided Conversation ID not found."}
        
        # Fetch the user_id and title
        user_id = original_conversation["userId"]  
        title = original_conversation["title"]  

        new_conversation = {  
            "id": conversation_id,  
            "conversation_id": conversation_id, 
            "user_id": user_id,
            "title": title, 
            "evaluated_message": [evaluated_message]  
        }

        # If conversation ID doesn't exist, append the message evaluation scores in a new item
        cosmos_client.create_item(cosmos_conversation_evaluation_client, new_conversation)  
        
    # Return the conversation with the evaluated message  
    updated_conversation = fetch_conversation(cosmos_client, cosmos_conversation_evaluation_client, conversation_id)  
    return updated_conversation