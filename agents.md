Main Agent Operational Logic

When a user query is received:

1. Apply guardrails to the query.
2. Decide if context retrieval (RAG) is required.
3. If required, retrieve relevant chunks from the Vector Database.
4. Build the final prompt using:
   - llm.txt rules
   - retrieved context
   - user query
5. Send the prompt to the LLM Hub.
6. Receive the response.
7. Send the response to the Evaluator.
8. If the evaluation fails:
   - Retry with adjusted prompt OR
   - Retry with a different LLM provider.
9. Return the final validated response to the user.
