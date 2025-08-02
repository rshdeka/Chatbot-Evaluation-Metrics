import json
import logging
import azure.functions as func
from Config import Config
from OpenAI import OpenAI
from CosmosClient import CosmosClient  
from metrics.evaluations.models.HistoryMessage import Conversation
from metrics.evaluations.qna_scores import qna_blueprint
from metrics.evaluations.QnAService import qna_processing_blueprint, process_qna_evaluation
from metrics.evaluations.QnASubscriber import QnASubscriber
from metrics.evaluations.ConversationService import process_conversation_evaluation  
from metrics.evaluations.ConversationSubscriber import ConversationSubscriber

app = func.FunctionApp()
app.register_blueprint(qna_blueprint)
app.register_blueprint(qna_processing_blueprint)
app.register_blueprint(QnASubscriber)
app.register_blueprint(ConversationSubscriber)
    


@app.function_name(name="QnAEvaluation")  
@app.route(route="QnAEvaluation", auth_level=func.AuthLevel.ANONYMOUS)  
def qna_evaluation_scores(req: func.HttpRequest) -> func.HttpResponse:  
    logging.info('Processing request to upsert QnA scores to CosmosDB.')
  
    try:
        # Get the params from request body
        req_body = req.get_json()  
        conversation_id = req_body.get('conversation_id')  
        query_id = req_body.get('query_id')  
        response_id = req_body.get('response_id')  
        context_id = req_body.get('context_id')  

        # Check if all the required params are provided
        if not conversation_id or not query_id or not response_id:  
            return func.HttpResponse(  
                json.dumps({"error": "Missing required parameters."}),  
                status_code=400,  
                mimetype="application/json"  
            )
        
        updated_conversation = process_qna_evaluation(conversation_id, query_id, response_id, context_id)  
        return func.HttpResponse(  
            json.dumps(updated_conversation),  
            status_code=200,  
            mimetype="application/json"  
        )
           
    except Exception as e:  
        logging.error(f"Error evaluating QnA scores: {str(e)}")  
        return func.HttpResponse(  
            json.dumps({"error": str(e)}),  
            status_code=500,  
            mimetype="application/json"  
        )