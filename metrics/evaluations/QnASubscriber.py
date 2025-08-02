import logging
import json
import azure.functions as func
from Config import Config
from QnAService import process_qna_evaluation


# Configure logging
logging.basicConfig(level=logging.INFO)

config = Config()
QnASubscriber = func.Blueprint()


def process_qna_event(event_data, http_context=False):  
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
  
        # Handle QnA Evaluation Event
        conversation_id = event_data["ConversationId"]  
        query_id = event_data["QuestionId"]  
        response_id = event_data["ResponseId"]  
        context_id = event_data["ContextId"]  

        # Ensure all required IDs are present  
        if not conversation_id or not query_id or not response_id:  
            logging.info("Missing required data in the event payload.") 
            if http_context:   
                return func.HttpResponse("Missing required data in the event payload.", status_code=400)  
            else:
                return

        logging.info(f"Extracted IDs - ConversationId: {conversation_id}, ResponseId: {response_id}, QueryId: {query_id}, ContextId: {context_id}")  

        # Calculate QnA scores  
        updated_conversation = process_qna_evaluation(conversation_id, query_id, response_id, context_id)  
        logging.info(f"Updated conversation: {updated_conversation}")
  
        logging.info("QnA evaluation processed successfully.")  
        if http_context:  
            return func.HttpResponse(body=json.dumps(updated_conversation, indent=4), status_code=200, mimetype="application/json")
  
    except Exception as e:  
        logging.error(f"Error evaluating QnA scores: {str(e)}")  
        if http_context:  
            return func.HttpResponse(f"Error processing QnA evaluation: {str(e)}", status_code=500)  
    

# Event Grid Trigger Function  
@QnASubscriber.function_name(name="ProcessQnaEvalEventGrid")  
@QnASubscriber.event_grid_trigger(arg_name="azeventgrid")  
def process_qna_eval_event_grid(azeventgrid: func.EventGridEvent):
    logging.info("QnA Evaluation EventGrid trigger processed an event.")

    # Extract data from the Event Grid event  
    event_data = azeventgrid.get_json()
    logging.info(f"Event data: {event_data}")

    return process_qna_event(event_data)


# HTTP Trigger Function  
@QnASubscriber.function_name(name="ProcessQnaEvalHttp")  
@QnASubscriber.route(route="qnaeval")  
def process_qna_eval_http(req: func.HttpRequest):
    logging.info("QnA Evaluation HTTP trigger processed an event.")

    try:
        event_data = req.get_json()
        logging.info(f"Event data: {event_data}")

        return process_qna_event(event_data, http_context=True)      # Pass http_context=True 
    except Exception as e:  
        logging.error(f"Error reading HTTP request data: {str(e)}")  
        return func.HttpResponse(f"Error reading HTTP request data: {str(e)}", status_code=400)