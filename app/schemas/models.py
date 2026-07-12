from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, default=0.0)
    quantity = Column(Integer, default=0)

    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    analysis_cache = relationship("AnalysisCache", back_populates="product", uselist=False, cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    body = Column(Text, nullable=False)

    product = relationship("Product", back_populates="reviews")


class AnalysisCache(Base):
    __tablename__ = "analysis_cache"

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    analysis = Column(Text, nullable=False)

    product = relationship("Product", back_populates="analysis_cache")
