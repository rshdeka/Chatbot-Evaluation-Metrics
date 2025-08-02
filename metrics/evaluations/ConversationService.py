import logging
import json
from Config import Config
from OpenAI import OpenAI
from CosmosClient import CosmosClient
from models.HistoryMessage import Conversation
from models.ConversationEvaluation import ConversationEvaluation
import json
from uuid import uuid4
import azure.functions as func
from azure.cosmos.exceptions import CosmosResourceNotFoundError


conv_processing_blueprint=func.Blueprint()


eval_prompt = """
            # System:
            - You are an AI assistant. You will be given a transcript of dialogue between a user and a bot. You need to read the transcript carefully and identify the main topic, question, or issue of the conversation, as well as the purpose and expectations of the interaction.
            - You need to rate all the bot responses together on a scale of 1 (poor) to 5 (excellent) for each of the following factors, and provide some feedback for improvement.
                - Accuracy and relevance: How well does the bot provide correct and reliable information or advice that matches the user's intent and expectations, and uses credible and up-to-date sources or references to support its claims? How well does the bot avoid any errors, inconsistencies, or misinformation in its responses, and cite its sources or evidence if applicable?
                - Coherence and completeness: How well does the bot maintain a logical and consistent flow of conversation that follows the user's input and the purpose of the dialogue, and provides all the relevant and necessary information or actions to address the user's query or issue, without leaving any gaps, ambiguities, or unanswered questions?
                - Engagement and tone: How well does the bot capture and maintain the user's interest and attention, and motivate them to continue the conversation or explore the topic further, using natural and conversational language, personality, and emotion? How appropriate and consistent is the bot's tone for the context, purpose, and audience of the conversation, and how well does it match or adapt to the user's tone and mood? Does the bot avoid being rude, sarcastic, condescending, or too formal or informal, and convey respect, empathy, and politeness?
                - Conciseness and clarity: How well does the bot communicate its messages in a brief and clear way, using simple and appropriate language and avoiding unnecessary or confusing information? How easy is it for the user to understand and follow the bot responses, and how well do they match the user's needs and expectations?
                - Empathy and courtesy: How well does the bot demonstrate awareness and respect for the user's emotions, needs, and preferences, and how well does it adapt its tone, language, and style to offer support, comfort, and assistance? Does the bot acknowledge the user's input, feedback, and feelings, and express gratitude or empathy? Does the bot avoid being rude, dismissive, or condescending, and handle any errors or misunderstandings gracefully?
                - For each factor, provide specific examples or quotes from the transcript to support your ratings and explain why you gave them.
            - Give an score value which is calculated by ( 0.3 * "accuracy and relevance" + 0.2 * "coherence and completeness" + 0.25 * "engagement and tone" + 0.15 * "conciseness and clarity" + 0.1 * "empathy and courtesy")
            - Give an overall impression of the quality and effectiveness of the responses and suggest any areas for improvement or commendation. Write it in "Overall".

            - If the bot responses are not directly related to the user's query or issue, or if the user's intent or expectations are unclear or ambiguous, explain how this affects the quality of the conversation and the ratings for each factor, and provide some suggestions for how the bot could handle these situations better.

            # Tips：
            - You can write your feedback as bullet points, sentences, or paragraphs, but make sure they are organized and easy to read.
            - You should rate and provide feedback for the whole conversation as a whole, not for each bot response individually. However, you can mention if some responses are better or worse than others, and why.
            - You should try to be objective and constructive in your evaluation, and use evidence and examples from the transcript to support your ratings and feedback. Avoid bias, subjectivity, or personal preferences, and use respectful and polite language.
            - The output should be in json format.


            # Example:
            Example Conversation:
            {
            "conversation": "User: Why is the sky blue?\nBot: The sky is blue because of the way the atmosphere scatters light.\nUser: How does it scatter light?\nBot: The atmosphere is made up of tiny particles, such as water vapor and dust. When light hits these particles, it is scattered in all directions.\nUser: Why does the sky turn red at sunset?\nBot: During the day, the sky is blue because blue light is scattered more than other colors. At sunset, the light travels a longer distance through the atmosphere, so more of the blue light is scattered out, leaving the red and yellow light."
            }
            Example Output:
            {
            "accuracy and relevance": 5,
            "coherence and completeness": 4,
            "engagement and tone": 3.5,
            "conciseness and clarity": 3,
            "empathy and courtesy": 3,
            "score": 3.925
            "overall": "The bot responses are clear and concise, but they do not provide any relevant or helpful information to answer the user's question about the sky. The bot could have explained the science behind why the sky is blue and why it turns red at sunset, and provided some references or sources to support its claims. The bot could also have asked the user to clarify their question, or asked some follow-up questions to better understand the user's intent and expectations."
            }
            don't include triple quotes in the response
            Conversation:
            {{conversation}}
            Output:
            """


def process_conversation_evaluation(conversation_id):
    config=Config()

    cosmos_client = CosmosClient()  
    cosmos_conversation_client = cosmos_client.get_containerdb_client(cosmos_client, config.COSMOS_CONTAINER_ID,"userId")  
    cosmos_user_session_client = cosmos_client.get_containerdb_client(cosmos_client, config.COSMOS_USER_SESSION_CONTAINER_ID,"id")
    
    conversation_data = cosmos_client.read_items(cosmos_conversation_client, f"SELECT * FROM c WHERE c.id = '{conversation_id}'")

    if conversation_data:  
        # Load data from transcription_analysis DB to the Databricks table and get the inserted IDs
        logging.info(f"Number of conversations found: {len(conversation_data)}")
        for conversation in conversation_data:  
            user_conversation:Conversation =Conversation.from_dict(conversation)
            # convert messages to string format 
            user_conversation_messages=convert_chat_history_to_conversation(user_conversation.messages)
        
            prompt =eval_prompt.replace("{{conversation}}",json.dumps(user_conversation_messages))
            openai=OpenAI()
        
            response=openai.call_gpt_endpoint(prompt=prompt)
            logging.info(response)

            evaluation_results = process_conversation_analysis(user_conversation, response, cosmos_client, cosmos_user_session_client)
            logging.info(f"Evaluation Results: {evaluation_results}")
            return evaluation_results
    
    else:  
        logging.info("No conversations found.")


def process_conversation_analysis(user_conversation, response,cosmos_client,cosmos_user_session_client):
    conversation_analysis_obj = ConversationEvaluation.to_dict({})
    conversation_analysis_obj.id = str(uuid4())
    conversation_analysis_obj.conversationId = user_conversation.id
    conversation_analysis_obj.accuracyAndRelevance = response.get("accuracy and relevance", 0)
    conversation_analysis_obj.coherenceAndCompleteness = response.get("coherence and completeness", 0)
    conversation_analysis_obj.engagementAndTone = response.get("engagement and tone", 0)
    conversation_analysis_obj.concisenessAndClarity = response.get("conciseness and clarity", 0)
    conversation_analysis_obj.empathyAndCourtesy = response.get("empathy and courtesy", 0)
    conversation_analysis_obj.score = response.get("score", 0)
    conversation_analysis_obj.overall = response.get("overall", "")
    
    evalResult = { 
        "accuracyAndRelevance": conversation_analysis_obj.accuracyAndRelevance,  
        "coherenceAndCompleteness": conversation_analysis_obj.coherenceAndCompleteness,  
        "engagementAndTone": conversation_analysis_obj.engagementAndTone,  
        "concisenessAndClarity": conversation_analysis_obj.concisenessAndClarity,  
        "empathyAndCourtesy": conversation_analysis_obj.empathyAndCourtesy,  
        "score": conversation_analysis_obj.score,  
        "overall": conversation_analysis_obj.overall  
    }

    try:
        # Retrieve the corresponding UserSession item using callId
        query = f"SELECT * FROM c WHERE c.callId = '{user_conversation.id}'"  
        user_session_items = cosmos_client.read_items(cosmos_user_session_client, query) 

        if user_session_items:  
            user_session_item = user_session_items[0]
            logging.info(f"UserSession item found: {user_session_item}")

            # If the UserSession item already exists, update the evalResult field
            user_session_item['isEvaluated'] = True
            user_session_item['evalResult'] = evalResult  
    
            # Update the required fields in the UserSession item
            cosmos_client.update_item(cosmos_user_session_client, json.loads(json.dumps(user_session_item, default=lambda x: x.__dict__)))  
            logging.info("User session updated successfully")
        else:  
            logging.error(f"UserSession item with callId {user_conversation.id} not found.")
        
    except CosmosResourceNotFoundError:
        # If the UserSession item does not exist, create a new one  
        logging.info(f"UserSession item not found. Creating new item with callId: {user_conversation.id}")  
        user_session_item = {  
            "id": user_conversation.id,
            "callId": user_conversation.id,
            "isEvaluated": True,  
            "evalResult": evalResult 
        }
        cosmos_client.create_item(cosmos_user_session_client, json.loads(json.dumps(user_session_item, default=lambda x: x.__dict__)))  
        logging.info("New user session created successfully")
    
    except Exception as e:  
        logging.error(f"An error occurred: {str(e)}") 

    return evalResult


def convert_chat_history_to_conversation(chat_history: list) -> dict:
    conversation=""
    filtered_messages = [message for message in chat_history if message["role"] in ["user", "assistant"]] 
    # Iterate through the messages array and format the conversation  
    for message in filtered_messages:  
        role = "User" if message["role"] == "user" else "Bot"  
        conversation += f"{role}:{message['content']}\n" 
    formatted_conversation = {  
    "conversation": conversation.strip()  # Strip any trailing newline  
    }  
    return formatted_conversation