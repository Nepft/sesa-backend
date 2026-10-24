"""Skema request untuk endpoint prediksi."""
from pydantic import BaseModel, Field


class PredictTextRequest(BaseModel):
    """Body request untuk analisis sentimen satu teks ulasan."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Teks ulasan yang akan dianalisis sentimennya.",
        examples=["aplikasinya bagus dan mudah dipakai"],
    )
