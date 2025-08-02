class ConversationEvaluation:
    id: str
    conversationId: str
    accuracyAndRelevance: float
    coherenceAndCompleteness: float
    engagementAndTone: float
    concisenessAndClarity: float
    empathyAndCourtesy: float
    score: float
    overall: str
    
    def __init__(self,id: str,conversationId: str, accuracyAndRelevance: float, coherenceAndCompleteness: float, engagementAndTone: float, concisenessAndClarity: float, empathyAndCourtesy: float, score: float, overall: str):
        self.id = id
        self.conversationId = conversationId
        self.accuracyAndRelevance = accuracyAndRelevance
        self.coherenceAndCompleteness = coherenceAndCompleteness
        self.engagementAndTone = engagementAndTone
        self.concisenessAndClarity = concisenessAndClarity
        self.empathyAndCourtesy = empathyAndCourtesy
        self.score = score
        self.overall = overall

    def to_dict(data: dict):
        return ConversationEvaluation(
            data.get("id"),
            data.get("conversationId"),
            data.get("accuracyAndRelevance"),
            data.get("coherenceAndCompleteness"),
            data.get("engagementAndTone"),
            data.get("concisenessAndClarity"),
            data.get("empathyAndCourtesy"),
            data.get("score"),
            data.get("overall")
        )