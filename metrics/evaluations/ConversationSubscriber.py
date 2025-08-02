import logging  
import json 
import azure.functions as func  
from Config import Config  
from CosmosClient import CosmosClient  
from ConversationService import process_conversation_evaluation  
  
# Configure logging  
logging.basicConfig(level=logging.INFO)

config = Config()  
ConversationSubscriber = func.Blueprint()  
  

def process_conversation_event(event_data, http_context=False):  
    try:
        logging.info(f"Received event data: {json.dumps(event_data, indent=4)}")

        # Validate event data  
        if not isinstance(event_data, dict):  
            logging.error("Invalid event data structure.") 
            if http_context: 
                return func.HttpResponse(  
                    body="Invalid event data structure.",  
                    status_code=400  
                )
            else:
                return
  
        # Handle Conversation Evaluation Event
        conversation_id = event_data["ConversationId"] 
  
        # Ensure all required data is present  
        if not conversation_id:  
            logging.info("Missing required data in the event payload.")  
            if http_context:
                return func.HttpResponse("Missing required data in the event payload.", status_code=400)
            else:
                return

        logging.info(f"Extracted ID - ConversationId: {conversation_id}")  
            
        # Process conversation evaluation  
        evaluation_results = process_conversation_evaluation(conversation_id)
        logging.info(f"Evaluation Results: {evaluation_results}")
  
        logging.info("Conversation evaluation processed successfully.")
        if http_context:
            return func.HttpResponse(body=json.dumps(evaluation_results, indent=4), status_code=200, mimetype="application/json")  
    
    except Exception as e:  
        logging.error(f"Error evaluating conversation: {str(e)}")
        if http_context:
            return func.HttpResponse(f"Error processing conversation evaluation: {str(e)}", status_code=500)  
  

# Event Grid Trigger Function  
@ConversationSubscriber.function_name(name="ProcessConvEvalEventGrid")  
@ConversationSubscriber.event_grid_trigger(arg_name="azeventgrid")  
def process_conv_eval_event_grid(azeventgrid: func.EventGridEvent):  
    logging.info("Conversation Evaluation EventGrid trigger processed an event.")  
    
    # Extract data from the Event Grid event  
    event_data = azeventgrid.get_json()  
    logging.info(f"Event data: {event_data}")  
    
    return process_conversation_event(event_data)  


# HTTP Trigger Function  
@ConversationSubscriber.function_name(name="ProcessConvEvalHttp")  
@ConversationSubscriber.route(route="conveval")  
def process_conv_eval_http(req: func.HttpRequest):  
    logging.info("Conversation Evaluation HTTP trigger processed an event.")  
    
    try:  
        event_data = req.get_json()  
        logging.info(f"Event data: {event_data}")  
    
        return process_conversation_event(event_data, http_context=True)     # Pass http_context=True
    except Exception as e:  
        logging.error(f"Error reading HTTP request data: {str(e)}")  
        return func.HttpResponse(f"Error reading HTTP request data: {str(e)}", status_code=400)