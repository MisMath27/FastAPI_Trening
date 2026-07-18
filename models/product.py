from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, Enum
from sqlalchemy.sql import false
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from core.database import Base


class ProductStatus(PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    count: Mapped[int] = mapped_column(default=0)
    description: Mapped[Optional[str]] = mapped_column(nullable=False)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, name="product_status"),
        nullable=False,
        server_default=ProductStatus.DRAFT.value
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false()
    )