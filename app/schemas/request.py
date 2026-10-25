"""Skema request untuk endpoint prediksi."""
from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings


class PredictTextRequest(BaseModel):
    """Body request untuk analisis sentimen satu teks ulasan."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=get_settings().max_text_length,
        description="Teks ulasan yang akan dianalisis sentimennya.",
        examples=["aplikasinya bagus dan mudah dipakai"],
    )

    @field_validator("text")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        """Tolak teks yang hanya spasi/tab/newline sebagai ulasan kosong."""
        if not value.strip():
            raise ValueError("Teks ulasan tidak boleh hanya berisi spasi.")
        return value
