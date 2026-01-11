from typing import Dict, Iterable, List, Optional, Tuple

import random

from .aihubmix import AIHubMixProvider
from .openai import OpenAIProvider
from .sora_hk import SoraHKProvider
from .base import ProviderClient
from ..store import STORE


def _collect_providers(
    model_id: str,
    required_durations: Optional[Iterable[int]] = None,
    required_resolutions: Optional[Iterable[str]] = None,
    requires_pro: bool = False,
    requires_image: bool = False,
) -> List[Tuple[str, List[str], Dict]]:
    model = STORE.get_model(model_id)
    if not model:
        raise ValueError("model_id not found")
    provider_map = model.get("provider_map", {})
    candidates: List[Tuple[str, List[str], Dict]] = []
    durations = set(required_durations or [])
    resolutions = set(required_resolutions or [])
    for provider_id, provider_model_ids in provider_map.items():
        provider = STORE.get_provider(provider_id)
        if not provider or not provider.get("enabled"):
            continue
        if not provider_model_ids:
            continue
        if requires_pro and not provider.get("supports_pro"):
            continue
        if requires_image and not provider.get("supports_image_to_video"):
            continue
        supported_durations = set(provider.get("supported_durations", []))
        supported_resolutions = set(provider.get("supported_resolutions", []))
        if durations and not durations.issubset(supported_durations):
            continue
        if resolutions and not resolutions.issubset(supported_resolutions):
            continue
        candidates.append((provider_id, provider_model_ids, provider))
    if not candidates:
        raise ValueError("no enabled provider for model")
    candidates.sort(key=lambda item: item[2].get("priority", 100))
    return candidates


def select_provider(
    model_id: str,
    routing_strategy: str = "default",
    required_durations: Optional[Iterable[int]] = None,
    required_resolutions: Optional[Iterable[str]] = None,
    requires_pro: bool = False,
    requires_image: bool = False,
) -> Tuple[str, str]:
    candidates = _collect_providers(
        model_id,
        required_durations=required_durations,
        required_resolutions=required_resolutions,
        requires_pro=requires_pro,
        requires_image=requires_image,
    )
    if routing_strategy == "weighted":
        provider_id, provider_model_ids, _ = _pick_weighted(candidates)
    else:
        provider_id, provider_model_ids, _ = candidates[0]
    provider_model_id = provider_model_ids[0]
    return provider_id, provider_model_id


def select_provider_candidates(
    model_id: str,
    routing_strategy: str = "default",
    required_durations: Optional[Iterable[int]] = None,
    required_resolutions: Optional[Iterable[str]] = None,
    requires_pro: bool = False,
    requires_image: bool = False,
) -> List[Tuple[str, str]]:
    candidates = _collect_providers(
        model_id,
        required_durations=required_durations,
        required_resolutions=required_resolutions,
        requires_pro=requires_pro,
        requires_image=requires_image,
    )
    if routing_strategy == "weighted":
        provider_id, provider_model_ids, _ = _pick_weighted(candidates)
        return [(provider_id, provider_model_ids[0])]
    return [(provider_id, provider_model_ids[0]) for provider_id, provider_model_ids, _ in candidates]


def get_provider_client(
    provider_id: str,
    model_id: Optional[str] = None,
    provider_model_id: Optional[str] = None,
) -> ProviderClient:
    if provider_id == "sora_hk":
        return SoraHKProvider(model_id=model_id, provider_model_id=provider_model_id)
    if provider_id == "openai":
        return OpenAIProvider(model_id=model_id, provider_model_id=provider_model_id)
    if provider_id == "aihubmix":
        return AIHubMixProvider(model_id=model_id, provider_model_id=provider_model_id)
    raise ValueError("provider_id not supported")


def _pick_weighted(
    candidates: List[Tuple[str, List[str], Dict]],
) -> Tuple[str, List[str], Dict]:
    weighted: List[Tuple[str, List[str], Dict]] = []
    for provider_id, provider_model_ids, provider in candidates:
        weight = int(provider.get("weight") or 1)
        weighted.extend([(provider_id, provider_model_ids, provider)] * max(weight, 1))
    return random.choice(weighted)
