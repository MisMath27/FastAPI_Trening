from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from core.database import Base


class ProductStatus(PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    count: Mapped[int] = mapped_column(default=0)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[ProductStatus] = mapped_column(
        SQLAlchemyEnum(ProductStatus, name="product_status"),
        nullable=False,
        server_default=ProductStatus.DRAFT.value
    )