import logging
from Config import Config
from CosmosClient import CosmosClient
import azure.functions as func
from azure.ai.evaluation import (  
    RelevanceEvaluator, CoherenceEvaluator, FluencyEvaluator, GroundednessEvaluator, SimilarityEvaluator, 
    F1ScoreEvaluator, RougeScoreEvaluator, RougeType, GleuScoreEvaluator, BleuScoreEvaluator, MeteorScoreEvaluator) 

config=Config()
model_config = {
    "azure_endpoint": config.AZURE_OPENAI_BASE,
    "api_key": config.AZURE_OPENAI_KEY,
    "azure_deployment": config.AZURE_OPENAI_MODEL,
    "api_version": config.AZURE_OPENAI_VERSION
}


qna_blueprint=func.Blueprint()


# Function to initialize Performance and quality evaluators
def initialize_evaluators():  
    return {  
        "relevance": RelevanceEvaluator(model_config),  
        "coherence": CoherenceEvaluator(model_config),  
        "fluency": FluencyEvaluator(model_config),  
        "groundedness": GroundednessEvaluator(model_config),
        "similarity": SimilarityEvaluator(model_config),
        "f1": F1ScoreEvaluator(),
        "rouge": RougeScoreEvaluator(rouge_type=RougeType.ROUGE_1),
        "gleu": GleuScoreEvaluator(),
        "bleu": BleuScoreEvaluator(),
        "meteor": MeteorScoreEvaluator()
    } 
 

# Function to fetch a specific conversation from CosmosDB container  
def fetch_conversation(cosmos_client, cosmos_conversation_client, conversation_id):  
    try:  
        query = f"SELECT * FROM c WHERE c.id = '{conversation_id}'"  
        conversation_data = cosmos_client.read_items(cosmos_conversation_client, query)  
        if conversation_data:  
            return conversation_data[0]  
        return None  
    except Exception as e:  
        logging.error(f"Error executing query on Cosmos DB: {str(e)}")  
        return None
    

# Function to get evaluations based on whether the context is present or not
def evaluate_message(evaluators, query, context, response):  
    scores = {}  
    
    if context:  
        scores['groundedness'] = evaluators['groundedness'](response=response, context=context)  
        scores['relevance'] = evaluators['relevance'](response=response, context=context, query=query)  
        scores['similarity'] = evaluators['similarity'](response=response, ground_truth=context, query=query)
        scores['f1'] = evaluators['f1'](response=response, ground_truth=context)
        rouge_scores = evaluators['rouge'](response=response, ground_truth=context)
        scores['rouge'] = {  
            'precision': rouge_scores.get('rouge_precision'),  
            'recall': rouge_scores.get('rouge_recall'),  
            'f1_score': rouge_scores.get('rouge_f1_score')  
        }
        scores['gleu'] = evaluators['gleu'](response=response, ground_truth=context)
        scores['bleu'] = evaluators['bleu'](response=response, ground_truth=context)
        scores['meteor'] = evaluators['meteor'](response=response, ground_truth=context)
    else:  
        scores['coherence'] = evaluators['coherence'](response=response, query=query)  
        scores['fluency'] = evaluators['fluency'](response=response, query=query)
    return scores  


# Main Function to calculate the scores
def calculate_qna_scores(conversation_id, query_id, response_id, context_id):
    logging.info('Processing request to evaluate QnA scores.') 

    # Initialize Evaluators  
    evaluators = initialize_evaluators() 

    # Connect to Cosmos DB  
    cosmos_client = CosmosClient()  
    cosmos_conversation_client = cosmos_client.get_containerdb_client(cosmos_client, config.COSMOS_CONTAINER_ID, "userId")  
    
    # Fetch the specific conversation  
    conversation = fetch_conversation(cosmos_client, cosmos_conversation_client, conversation_id)  
    if not conversation:  
        logging.info("Conversation not found.")  
        return {"error": f"Provided Conversation ID not found."} 
  
    logging.info(f"Processing conversation ID: {conversation_id} with {len(conversation['messages'])} messages.")

    messages = conversation["messages"]

    # Find specific messages based on query_id, response_id, and context_id  
    query_message = next((msg for msg in messages if msg["messageId"] == query_id and msg["role"] == "user"), None)
    response_message = next((msg for msg in messages if msg["messageId"] == response_id and msg["role"] == "assistant"), None)  
    context_message = next((msg for msg in messages if msg["messageId"] == context_id and msg["role"] == "tool"), None)

    if query_message is None or response_message is None:  
        logging.error("Query message or Response message not found.")  
        return {
            "error": "Query message or Response message not found."
        }
    
    query = query_message["content"]  
    response = response_message["content"]  
    context = context_message["content"] if context_message else ""

    # Get the scores from the Evaluators  
    eval_scores = evaluate_message(evaluators, query, context, response)

    # Structure the evaluated messages
    evaluated_message = { 
        "query_id": query_id,  
        "response_id": response_id,  
        "context_id": context_id,  
        "scores": {} 
    }

    if context_id:
        evaluated_message["scores"].update({
            "relevance_score": eval_scores.get("relevance", {}).get("gpt_relevance"),  
            "groundedness_score": eval_scores.get("groundedness", {}).get("gpt_groundedness"),  
            "similarity_score": eval_scores.get("similarity", {}).get("gpt_similarity"),
            "f1_score": eval_scores.get("f1", {}).get("f1_score"),
            "rouge_score": {  
                "precision": eval_scores.get("rouge", {}).get("precision"),  
                "recall": eval_scores.get("rouge", {}).get("recall"),  
                "f1_score": eval_scores.get("rouge", {}).get("f1_score")  
            }, 
            "gleu_score": eval_scores.get("gleu", {}).get("gleu_score"),
            "bleu_score": eval_scores.get("bleu", {}).get("bleu_score"),
            "meteor_score": eval_scores.get("meteor", {}).get("meteor_score")
        })
    else:
        evaluated_message["scores"].update({  
            "coherence_score": eval_scores.get("coherence", {}).get("gpt_coherence"),  
            "fluency_score": eval_scores.get("fluency", {}).get("gpt_fluency")  
        })  

    return evaluated_message