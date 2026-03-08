"""
Defense configuration for memory injection evaluations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


BEGIN_UNTRUSTED_DOCUMENT = "BEGIN_UNTRUSTED_DOCUMENT"
END_UNTRUSTED_DOCUMENT = "END_UNTRUSTED_DOCUMENT"

VALID_DEFENSES = {
    "system_prompt_hardening",
    "untrusted_content_markers",
}


@dataclass(frozen=True)
class DefenseConfig:
    """Per-eval defenses that can be enabled independently."""

    system_prompt_hardening: bool = False
    untrusted_content_markers: bool = False

    def to_metadata(self) -> dict[str, bool]:
        return asdict(self)


def defense_config_from_names(names: list[str] | None) -> DefenseConfig:
    """Build a defense config from CLI-friendly defense names."""
    if not names:
        return DefenseConfig()

    normalized = {name.strip() for name in names if name.strip()}
    unknown = sorted(normalized - VALID_DEFENSES)
    if unknown:
        raise ValueError(
            f"Unknown defenses: {unknown}. Available: {sorted(VALID_DEFENSES)}"
        )

    return DefenseConfig(
        system_prompt_hardening="system_prompt_hardening" in normalized,
        untrusted_content_markers="untrusted_content_markers" in normalized,
    )


def wrap_untrusted_document(content: str) -> str:
    """Wrap retrieved document text in explicit untrusted-content markers."""
    return f"{BEGIN_UNTRUSTED_DOCUMENT}\n{content}\n{END_UNTRUSTED_DOCUMENT}"
