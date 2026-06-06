class InteractionStore:
    """Persist exposed chatbot interactions without duplicating retrieved chunk text."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        id_factory: Callable[[], str] | None = None,
        timestamp_factory: Callable[[], str] | None = None,
    ) -> None:
        if not str(db_path).strip():
            raise ValueError("db_path must be a non-empty path")
        self._db_path = Path(db_path)
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._timestamp_factory = timestamp_factory or self._utc_timestamp

    @property
    def db_path(self) -> Path:
        """Return the configured database path."""

        return self._db_path

    def initialize(self) -> None:
        """Create the interaction schema if it does not already exist."""

        with closing(self._connect()) as connection, connection:
            self._initialize_schema(connection)

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

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.execute(CREATE_INTERACTIONS_TABLE)
        connection.execute(CREATE_RETRIEVED_CHUNK_REFS_TABLE)
        connection.execute(CREATE_INTERACTIONS_CREATED_AT_INDEX)
        connection.execute(CREATE_CHUNK_REFS_CHUNK_ID_INDEX)

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

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
