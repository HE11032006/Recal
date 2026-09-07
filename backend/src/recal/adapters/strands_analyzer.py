from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, cast

from pydantic import BaseModel, Field, HttpUrl

from recal.application.ports import OpportunityAnalysisPort, SearchResult
from recal.domain.entities import Opportunity, OpportunityType, UserProfile


class ExtractedOpportunity(BaseModel):
    """Schéma strict demandé au modèle pour une opportunité."""

    type: OpportunityType
    title: str = Field(min_length=1)
    organization: str = ""
    summary: str = Field(min_length=1)
    source_url: HttpUrl
    deadline: date | None = None
    eligibility: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0, le=100)
    relevance_reasons: list[str] = Field(default_factory=list)
    interest_fit: float = Field(ge=0, le=100)
    eligibility_fit: float = Field(ge=0, le=100)
    country_fit: float = Field(ge=0, le=100)
    freshness: float = Field(ge=0, le=100)
    source_quality: float = Field(ge=0, le=100)


class ExtractedOpportunities(BaseModel):
    opportunities: list[ExtractedOpportunity] = Field(default_factory=list)


class StrandsOpportunityAnalyzer(OpportunityAnalysisPort):
    """Analyseur Strands utilisant un modèle Amazon Bedrock.

    L’import de Strands est différé à l’instanciation afin que le domaine et les
    tests locaux restent exécutables sans installer le SDK ni configurer AWS.
    """

    def __init__(
        self,
        *,
        model_id: str,
        region_name: str = "us-east-1",
        max_tokens: int = 4000,
    ) -> None:
        try:
            from strands import Agent
            from strands.models import BedrockModel
        except ImportError as exc:  # pragma: no cover - dépendance optionnelle
            raise RuntimeError(
                "Installez l’extra backend[agent] avant d’utiliser Strands."
            ) from exc

        self._agent = Agent(
            model=BedrockModel(
                model_id=model_id,
                region_name=region_name,
                temperature=0.1,
                max_tokens=max_tokens,
                streaming=False,
            ),
            system_prompt=(
                "Tu es un analyste strict d'opportunités pour étudiants tech. "
                "N'invente jamais une date, une condition ou une URL. "
                "Ignore les pages qui ne décrivent pas une opportunité réelle."
            ),
            callback_handler=None,
        )

    async def analyze(
        self,
        search_results: Sequence[SearchResult],
        profile: UserProfile,
    ) -> list[Opportunity]:
        context = "\n\n".join(
            f"SOURCE {index}:\nTitre: {item.title}\nURL: {item.url}\nContenu: {item.content[:6000]}"
            for index, item in enumerate(search_results, start=1)
        )
        prompt = f"""
Profil utilisateur:
- Intérêts: {", ".join(profile.interests)}
- Pays: {", ".join(profile.countries)}
- Niveau: {profile.study_level}
- Compétences: {", ".join(profile.skills)}

Résultats web à analyser:
{context}

Extrait uniquement les opportunités pertinentes. Retourne une liste vide si aucune
opportunité n'est suffisamment fiable. L'URL source doit être une URL présente
dans les résultats fournis.
"""
        result = await self._agent.invoke_async(
            prompt,
            structured_output_model=ExtractedOpportunities,
        )
        if result.structured_output is None:
            return []
        extracted = cast(ExtractedOpportunities, result.structured_output)
        opportunities: list[Opportunity] = []
        for item in extracted.opportunities:
            final_score = self._score(item)
            opportunity = Opportunity(
                id=self._stable_id(str(item.source_url), item.title),
                type=item.type,
                title=item.title,
                organization=item.organization,
                summary=item.summary,
                source_url=str(item.source_url),
                relevance_score=final_score,
                confidence_score=item.confidence_score,
                relevance_reasons=item.relevance_reasons,
                deadline=item.deadline,
                eligibility=item.eligibility,
            )
            opportunity.validate()
            opportunities.append(opportunity)
        return opportunities

    @staticmethod
    def _score(item: ExtractedOpportunity) -> float:
        return round(
            item.interest_fit * 0.35
            + item.eligibility_fit * 0.25
            + item.country_fit * 0.15
            + item.freshness * 0.15
            + item.source_quality * 0.10,
            2,
        )

    @staticmethod
    def _stable_id(url: str, title: str) -> str:
        import hashlib

        normalized = f"{url.strip().lower()}|{title.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
