class InteractionStore:
    def save_interaction(
        self,
        *,
        request: QueryRequest,
        response: OrchestratorResponse,
        endpoint: str,
        session_id: str | None = None,
    ) -> str:
        """Save one final response and its returned chunk references atomically."""

        if not endpoint.strip():
            raise ValueError("endpoint must be a non-empty string")

        interaction_id = self._id_factory()
        created_at = self._timestamp_factory()
        with closing(self._connect()) as connection, connection:
            self._initialize_schema(connection)
            self._insert_interaction(
                connection,
                interaction_id=interaction_id,
                created_at=created_at,
                session_id=session_id,
                endpoint=endpoint,
                request=request,
                response=response,
            )
            self._insert_chunk_references(
                connection,
                interaction_id=interaction_id,
                response=response,
            )
        return interaction_id

    @staticmethod
    def _insert_interaction(
        connection: sqlite3.Connection,
        *,
        interaction_id: str,
        created_at: str,
        session_id: str | None,
        endpoint: str,
        request: QueryRequest,
        response: OrchestratorResponse,
    ) -> None:
        retrieval = response.retrieval
        evaluator = response.evaluator
        connection.execute(
            """
            INSERT INTO interactions (
                id, created_at, session_id, endpoint, user_query, assistant_response,
                provider, model, retries, guardrail_valid, guardrail_category,
                guardrail_reason_code, evaluator_passed, evaluator_score,
                retrieval_provenance, retrieval_hit_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interaction_id,
                created_at,
                session_id,
                endpoint,
                request.query,
                response.response,
                response.provider,
                response.model,
                response.retries,
                int(response.guardrail.is_valid),
                response.guardrail.category,
                response.guardrail.reason_code,
                int(evaluator.passed) if evaluator is not None else None,
                evaluator.score if evaluator is not None else None,
                retrieval.provenance if retrieval is not None else None,
                len(retrieval.hits) if retrieval is not None else 0,
            ),
        )

    @staticmethod
    def _insert_chunk_references(
        connection: sqlite3.Connection,
        *,
        interaction_id: str,
        response: OrchestratorResponse,
    ) -> None:
        if response.retrieval is None:
            return
        rows = [
            (
                interaction_id,
                rank,
                hit.chunk_id,
                hit.score,
                hit.source,
                hit.source_file,
                hit.page,
                hit.section,
            )
            for rank, hit in enumerate(response.retrieval.hits, start=1)
        ]
        if not rows:
            return
        connection.executemany(
            """
            INSERT INTO retrieved_chunk_refs (
                interaction_id, rank, chunk_id, score, source, source_file, page, section
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
